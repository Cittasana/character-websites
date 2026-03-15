"""
Character-Websites Backend API
FastAPI application entry point with Uvicorn multi-worker config.
"""
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import get_settings
from app.database import check_db_health, engine
from app.middleware.audit import AuditMiddleware
from app.middleware.security import SecurityHeadersMiddleware

# ── Logging ───────────────────────────────────────────────────────────────────
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
)
logger = structlog.get_logger()

settings = get_settings()

# ── Rate Limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("startup", app=settings.APP_NAME, env=settings.APP_ENV)
    # Validate DB connectivity at startup
    if not await check_db_health():
        logger.error("database_unreachable")
        raise RuntimeError("Cannot connect to PostgreSQL on startup")
    logger.info("database_connected")

    # Run security checks in production
    if settings.APP_ENV == "production":
        from app.security_checks import run_all_security_checks
        sec_result = await run_all_security_checks()
        if not sec_result["all_passed"]:
            for issue in sec_result["issues"]:
                logger.error("security_check_failed", issue=issue)
        else:
            logger.info("security_checks_passed")

    yield
    # Shutdown: dispose connection pool
    await engine.dispose()
    logger.info("shutdown")


# ── App Factory ───────────────────────────────────────────────────────────────
def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # ── Middleware (order matters: first added = outermost) ────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(AuditMiddleware)

    # ── Rate Limiter ───────────────────────────────────────────────────────
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore

    # ── Routers ────────────────────────────────────────────────────────────
    from app.auth.router import router as auth_router
    from app.routes.upload.voice import router as voice_router
    from app.routes.upload.photo import router as photo_router
    from app.routes.upload.transcript import router as transcript_router
    from app.routes.retrieve.website import router as website_router
    from app.routes.retrieve.personality import router as personality_router
    from app.routes.retrieve.voiceclips import router as voiceclips_router
    from app.routes.retrieve.qa import router as qa_router

    app.include_router(auth_router)
    app.include_router(voice_router)
    app.include_router(photo_router)
    app.include_router(transcript_router)
    app.include_router(website_router)
    app.include_router(personality_router)
    app.include_router(voiceclips_router)
    app.include_router(qa_router)

    # ── Exception Handlers ─────────────────────────────────────────────────
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors(), "body": str(exc.body)},
        )

    # ── Health Check ───────────────────────────────────────────────────────
    @app.get("/health", tags=["meta"], include_in_schema=False)
    async def health_check() -> dict:
        db_ok = await check_db_health()
        return {
            "status": "ok" if db_ok else "degraded",
            "database": "connected" if db_ok else "unreachable",
            "version": settings.APP_VERSION,
        }

    @app.get("/", tags=["meta"], include_in_schema=False)
    async def root() -> dict:
        return {"service": settings.APP_NAME, "version": settings.APP_VERSION}

    return app


app = create_app()
