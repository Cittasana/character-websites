"""
Audit logging middleware — logs all upload events to the audit_logs table.
Runs after each request so it can capture the response status code.
"""
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from jose import JWTError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.auth.security import verify_token
from app.database import AsyncSessionLocal
from app.models.audit_log import AuditLog

# Only audit these path prefixes (adjust as needed)
_AUDIT_PATHS = ("/api/upload/", "/api/retrieve/", "/api/auth/login", "/api/auth/register")


class AuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs all ingest and auth events to the audit_logs table.
    Does NOT block the request — failures are swallowed to avoid impacting users.
    """

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Only audit specific routes
        path = request.url.path
        should_audit = any(path.startswith(p) for p in _AUDIT_PATHS)

        start_time = time.monotonic()
        response = await call_next(request)
        duration_ms = int((time.monotonic() - start_time) * 1000)

        if should_audit:
            try:
                await self._write_audit_log(request, response.status_code, duration_ms)
            except Exception:
                # Never let audit failures break the API
                pass

        return response

    async def _write_audit_log(
        self,
        request: Request,
        status_code: int,
        duration_ms: int,
    ) -> None:
        # Try to extract user_id from JWT (best-effort)
        user_id: uuid.UUID | None = None
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                payload = verify_token(auth_header[7:], expected_type="access")
                user_id = uuid.UUID(payload.sub)
            except (JWTError, ValueError):
                pass

        # Determine event type from path
        path = request.url.path
        if "/upload/voice" in path:
            event_type = "upload.voice"
        elif "/upload/photo" in path:
            event_type = "upload.photo"
        elif "/upload/transcript" in path:
            event_type = "upload.transcript"
        elif "/retrieve/website" in path:
            event_type = "retrieve.website"
        elif "/retrieve/personality" in path:
            event_type = "retrieve.personality"
        elif "/retrieve/voiceclips" in path:
            event_type = "retrieve.voiceclips"
        elif "/retrieve/qa" in path:
            event_type = "retrieve.qa"
        elif "/auth/login" in path:
            event_type = "auth.login"
        elif "/auth/register" in path:
            event_type = "auth.register"
        else:
            event_type = f"{request.method.lower()}.{path.strip('/').replace('/', '.')}"

        async with AsyncSessionLocal() as session:
            log = AuditLog(
                user_id=user_id,
                event_type=event_type,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                request_path=path,
                request_method=request.method,
                response_status=status_code,
                metadata={"duration_ms": duration_ms},
            )
            session.add(log)
            await session.commit()
