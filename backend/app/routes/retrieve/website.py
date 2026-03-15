"""
GET /api/retrieve/website/:userId
Returns full website schema JSON for rendering by the Next.js frontend.
Read-only — session validation required before any data is served.
Redis-cached with 1hr TTL, invalidated on new analysis.
"""
import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user
from app.cache import cache_get, cache_set, make_cache_key
from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.models.website_config import WebsiteConfig
from slowapi import Limiter
from slowapi.util import get_remote_address

settings = get_settings()
router = APIRouter(prefix="/api/retrieve", tags=["retrieve"])
limiter = Limiter(key_func=get_remote_address)


class WebsiteSchemaResponse(BaseModel):
    user_id: uuid.UUID
    website_config_id: uuid.UUID
    version: int
    subdomain: str | None
    site_mode: str
    config: dict[str, Any]
    is_published: bool
    last_rendered_at: str | None
    cached: bool = False


@router.get(
    "/website/{user_id}",
    response_model=WebsiteSchemaResponse,
    summary="Get full website schema for a user",
    description=(
        "Returns the complete website configuration JSON for rendering. "
        "Read-only endpoint. JWT required. Redis-cached 1hr."
    ),
)
@limiter.limit(settings.RATE_LIMIT_RETRIEVE)
async def get_website_schema(
    request: Request,
    user_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WebsiteSchemaResponse:
    # Users can only fetch their own website config
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # ── Cache check ───────────────────────────────────────────────────────
    cache_key = make_cache_key("website", str(user_id))
    cached_data = await cache_get(cache_key)
    if cached_data:
        return WebsiteSchemaResponse(**cached_data, cached=True)

    # ── DB query (RLS enforced by set_rls_user in auth dependency) ─────────
    result = await db.execute(
        select(WebsiteConfig)
        .where(WebsiteConfig.user_id == user_id)
        .order_by(WebsiteConfig.updated_at.desc())
        .limit(1)
    )
    website_config = result.scalar_one_or_none()

    if website_config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No website configuration found. Upload a voice recording first.",
        )

    response_data = {
        "user_id": str(user_id),
        "website_config_id": str(website_config.id),
        "version": website_config.version,
        "subdomain": website_config.subdomain,
        "site_mode": website_config.site_mode,
        "config": website_config.config,
        "is_published": website_config.is_published,
        "last_rendered_at": website_config.last_rendered_at.isoformat()
        if website_config.last_rendered_at else None,
        "cached": False,
    }

    # ── Cache response ────────────────────────────────────────────────────
    await cache_set(cache_key, response_data, ttl=settings.CACHE_TTL_SECONDS)

    return WebsiteSchemaResponse(**response_data)
