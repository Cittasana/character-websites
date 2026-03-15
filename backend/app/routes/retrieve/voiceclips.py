"""
GET /api/retrieve/voiceclips/:userId
Returns voice clip metadata with 1hr signed Supabase Storage URLs.
Read-only. JWT required.
"""
import uuid
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.auth.dependencies import get_current_active_user
from app.config import get_settings
from app.storage import get_storage_service
from app.supabase_client import get_supabase

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
    summary="Get voice clip metadata with signed Supabase Storage URLs",
    description=(
        "Returns all voice clips for a user with 1hr signed download URLs. "
        "Read-only. JWT required. Signed URLs expire after 1 hour."
    ),
)
@limiter.limit(settings.RATE_LIMIT_RETRIEVE)
async def get_voice_clips(
    request: Request,
    user_id: uuid.UUID,
    current_user: Annotated[dict, Depends(get_current_active_user)],
) -> VoiceClipsResponse:
    if str(current_user.id) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # ── DB query ──────────────────────────────────────────────────────────
    supabase = get_supabase()
    result = supabase.table("voice_clips").select("*").eq(
        "user_id", str(user_id)
    ).order("display_order", desc=False).order("created_at", desc=False).execute()

    clips = result.data or []

    # ── Generate signed URLs (1hr expiry) ─────────────────────────────────
    storage = get_storage_service()
    clip_items: List[VoiceClipItem] = []

    for clip in clips:
        try:
            signed_url = storage.get_signed_url(
                bucket=clip.get("storage_bucket", "voice-clips"),
                path=clip["storage_path"],
                expires_in=3600,
            )
        except Exception:
            signed_url = ""  # Don't fail the whole response for one bad URL

        clip_items.append(
            VoiceClipItem(
                clip_id=uuid.UUID(clip["id"]),
                label=clip.get("label"),
                duration_seconds=clip.get("duration_seconds", 0.0),
                file_size_bytes=clip.get("file_size_bytes", 0),
                mime_type=clip.get("mime_type", "audio/mpeg"),
                display_order=clip.get("display_order", 0),
                signed_url=signed_url,
                url_expires_in_seconds=3600,
                created_at=clip.get("created_at", ""),
            )
        )

    return VoiceClipsResponse(
        user_id=user_id,
        clips=clip_items,
        total=len(clip_items),
    )
