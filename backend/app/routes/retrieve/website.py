"""
GET /api/retrieve/website/:userId
Returns full website schema JSON for rendering by the Next.js frontend.
Read-only — JWT authentication required.
Redis-cached with 1hr TTL, invalidated on new analysis.
Uses Supabase RPC get_website_data(username) for public lookups,
direct table query for authenticated user lookups.
"""
import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.auth.dependencies import get_current_active_user
from app.cache import cache_get, cache_set, make_cache_key
from app.config import get_settings
from app.supabase_client import get_supabase

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
    current_user: Annotated[dict, Depends(get_current_active_user)],
) -> WebsiteSchemaResponse:
    # Users can only fetch their own website config
    if str(current_user.id) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # ── Cache check ───────────────────────────────────────────────────────
    cache_key = make_cache_key("website", str(user_id))
    cached_data = await cache_get(cache_key)
    if cached_data:
        return WebsiteSchemaResponse(**cached_data, cached=True)

    # ── DB query ──────────────────────────────────────────────────────────
    supabase = get_supabase()
    result = supabase.table("website_configs").select("*").eq(
        "user_id", str(user_id)
    ).order("updated_at", desc=True).limit(1).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No website configuration found. Upload a voice recording first.",
        )

    wc = result.data[0]

    response_data = {
        "user_id": str(user_id),
        "website_config_id": wc["id"],
        "version": wc.get("version", 1),
        "subdomain": wc.get("subdomain"),
        "site_mode": wc.get("site_mode", "cv"),
        "config": wc.get("config", {}),
        "is_published": wc.get("is_published", False),
        "last_rendered_at": wc.get("last_rendered_at"),
        "cached": False,
    }

    # ── Cache response ────────────────────────────────────────────────────
    await cache_set(cache_key, response_data, ttl=settings.CACHE_TTL_SECONDS)

    return WebsiteSchemaResponse(**response_data)
