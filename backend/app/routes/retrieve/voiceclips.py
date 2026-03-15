"""
GET /api/retrieve/voiceclips/:userId
Returns voice clip metadata with 1hr signed S3 URLs.
Read-only. JWT required.
"""
import uuid
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user
from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.models.voice_clip import VoiceClip
from app.storage import generate_presigned_url
from slowapi import Limiter
from slowapi.util import get_remote_address

settings = get_settings()
router = APIRouter(prefix="/api/retrieve", tags=["retrieve"])
limiter = Limiter(key_func=get_remote_address)


class VoiceClipItem(BaseModel):
    clip_id: uuid.UUID
    label: str | None
    duration_seconds: float
    file_size_bytes: int
    mime_type: str
    display_order: int
    signed_url: str
    url_expires_in_seconds: int
    created_at: str


class VoiceClipsResponse(BaseModel):
    user_id: uuid.UUID
    clips: List[VoiceClipItem]
    total: int


@router.get(
    "/voiceclips/{user_id}",
    response_model=VoiceClipsResponse,
    summary="Get voice clip metadata with signed S3 URLs",
    description=(
        "Returns all voice clips for a user with 1hr signed download URLs. "
        "Read-only. JWT required. Signed URLs expire after 1 hour."
    ),
)
@limiter.limit(settings.RATE_LIMIT_RETRIEVE)
async def get_voice_clips(
    request: Request,
    user_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> VoiceClipsResponse:
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # ── DB query (RLS enforced) ───────────────────────────────────────────
    result = await db.execute(
        select(VoiceClip)
        .where(VoiceClip.user_id == user_id)
        .order_by(VoiceClip.display_order.asc(), VoiceClip.created_at.asc())
    )
    clips = result.scalars().all()

    # ── Generate signed URLs (1hr expiry) ─────────────────────────────────
    # Note: presigned URL generation is fast (local HMAC) — no network call
    clip_items: List[VoiceClipItem] = []
    for clip in clips:
        try:
            signed_url = generate_presigned_url(
                s3_key=clip.s3_key,
                bucket=clip.s3_bucket,
                expiry=3600,  # 1 hour
            )
        except Exception:
            signed_url = ""  # Don't fail the whole response for one bad URL

        clip_items.append(
            VoiceClipItem(
                clip_id=clip.id,
                label=clip.label,
                duration_seconds=clip.duration_seconds,
                file_size_bytes=clip.file_size_bytes,
                mime_type=clip.mime_type,
                display_order=clip.display_order,
                signed_url=signed_url,
                url_expires_in_seconds=3600,
                created_at=clip.created_at.isoformat(),
            )
        )

    return VoiceClipsResponse(
        user_id=user_id,
        clips=clip_items,
        total=len(clip_items),
    )
