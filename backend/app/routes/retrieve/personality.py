"""
GET /api/retrieve/personality/:userId
Returns personality dimension scores and full schema for the current version.
Read-only. JWT required. Redis-cached.
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
from app.models.personality_schema import PersonalitySchema
from app.models.user import User
from slowapi import Limiter
from slowapi.util import get_remote_address

settings = get_settings()
router = APIRouter(prefix="/api/retrieve", tags=["retrieve"])
limiter = Limiter(key_func=get_remote_address)


class PersonalityResponse(BaseModel):
    user_id: uuid.UUID
    schema_id: uuid.UUID
    version: int
    claude_model: str
    dimensions: dict[str, Any]
    persona_blend: dict[str, Any]
    color_palette: dict[str, Any]
    typography: dict[str, Any]
    layout: dict[str, Any]
    animation: dict[str, Any]
    cv_content: dict[str, Any] | None
    dating_content: dict[str, Any] | None
    created_at: str
    cached: bool = False


@router.get(
    "/personality/{user_id}",
    response_model=PersonalityResponse,
    summary="Get personality dimension scores",
    description=(
        "Returns the current personality analysis for a user. "
        "Read-only. JWT required. Redis-cached 1hr."
    ),
)
@limiter.limit(settings.RATE_LIMIT_RETRIEVE)
async def get_personality(
    request: Request,
    user_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PersonalityResponse:
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # ── Cache check ───────────────────────────────────────────────────────
    cache_key = make_cache_key("personality", str(user_id))
    cached_data = await cache_get(cache_key)
    if cached_data:
        return PersonalityResponse(**cached_data, cached=True)

    # ── DB query ──────────────────────────────────────────────────────────
    result = await db.execute(
        select(PersonalitySchema)
        .where(
            PersonalitySchema.user_id == user_id,
            PersonalitySchema.is_current == True,  # noqa: E712
        )
        .order_by(PersonalitySchema.created_at.desc())
        .limit(1)
    )
    schema = result.scalar_one_or_none()

    if schema is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No personality analysis found. Upload a voice recording first.",
        )

    response_data = {
        "user_id": str(user_id),
        "schema_id": str(schema.id),
        "version": schema.version,
        "claude_model": schema.claude_model,
        "dimensions": schema.dimensions,
        "persona_blend": schema.persona_blend,
        "color_palette": schema.color_palette,
        "typography": schema.typography,
        "layout": schema.layout,
        "animation": schema.animation,
        "cv_content": schema.cv_content,
        "dating_content": schema.dating_content,
        "created_at": schema.created_at.isoformat(),
        "cached": False,
    }

    await cache_set(cache_key, response_data, ttl=settings.CACHE_TTL_SECONDS)

    return PersonalityResponse(**response_data)
