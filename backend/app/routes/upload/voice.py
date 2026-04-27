"""
POST /api/upload/voice — multipart audio file upload.
Requirements:
- JWT authentication required
- File type validated via magic bytes (not extension)
- Max 50MB
- Files stored in Supabase Storage (voice-recordings bucket)
- Upload event logged to audit_logs
- Triggers async Celery analysis job
"""
import hashlib
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.auth.dependencies import get_current_active_user
from app.config import get_settings
from app.file_validation import validate_voice_file
from app.storage import get_storage_service
from app.supabase_client import get_supabase

settings = get_settings()
router = APIRouter(prefix="/api/upload", tags=["upload"])
limiter = Limiter(key_func=get_remote_address)


class VoiceUploadResponse(BaseModel):
    recording_id: uuid.UUID
    storage_path: str
    original_filename: str
    file_size_bytes: int
    detected_mime: str
    processing_status: str
    message: str


@router.post(
    "/voice",
    response_model=VoiceUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload a voice recording",
    description=(
        "Upload an audio file (MP3/WAV/M4A). Max 50MB. "
        "File type is validated server-side via magic bytes. "
        "Triggers async personality analysis."
    ),
)
@limiter.limit(settings.RATE_LIMIT_UPLOADS)
async def upload_voice(
    request: Request,
    file: Annotated[UploadFile, File(description="Audio file: mp3, wav, or m4a")],
    current_user: Annotated[dict, Depends(get_current_active_user)],
) -> VoiceUploadResponse:
    user_id = str(current_user.id)

    # ── Read file bytes ───────────────────────────────────────────────────
    file_data = await file.read()
    file_size = len(file_data)

    # ── Validate via magic bytes ──────────────────────────────────────────
    validation = validate_voice_file(file_data, file_size)
    if not validation.valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=validation.error,
        )

    # ── Compute SHA-256 for deduplication ─────────────────────────────────
    sha256 = hashlib.sha256(file_data).hexdigest()

    # ── Upload to Supabase Storage ────────────────────────────────────────
    original_filename = file.filename or "upload.audio"
    unique_filename = f"{uuid.uuid4()}_{original_filename}"
    storage = get_storage_service()

    try:
        storage_path = storage.upload_voice(
            user_id=user_id,
            filename=unique_filename,
            file_bytes=file_data,
            content_type=validation.detected_mime,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Storage upload failed: {exc}",
        )

    # ── Persist recording row ─────────────────────────────────────────────
    supabase = get_supabase()
    recording_data = {
        "user_id": user_id,
        "storage_path": storage_path,
        "storage_bucket": "voice-recordings",
        "original_filename": original_filename,
        "file_size_bytes": file_size,
        "mime_type": validation.detected_mime,
        "sha256": sha256,
        "processing_status": "pending",
    }

    try:
        result = supabase.table("recordings").insert(recording_data).execute()
        recording_id = result.data[0]["id"]
        processing_status = "pending"
    except Exception as exc:
        # Roll back storage upload if DB insert fails
        try:
            storage.delete_file("voice-recordings", storage_path)
        except Exception:
            pass
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database insert failed: {exc}",
        )

    # ── Audit log ─────────────────────────────────────────────────────────
    try:
        supabase.table("audit_logs").insert(
            {
                "user_id": user_id,
                "event_type": "upload.voice",
                "resource_type": "recording",
                "resource_id": recording_id,
                "ip_address": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
                "request_path": str(request.url.path),
                "request_method": "POST",
                "response_status": 202,
                "metadata": {
                    "file_size_bytes": file_size,
                    "mime_type": validation.detected_mime,
                    "storage_path": storage_path,
                },
            }
        ).execute()
    except Exception:
        pass  # Audit failure must not block the response

    # ── Trigger debounced Celery analysis ────────────────────────────────
    # Voice uploads land here from the Omi sync orchestrator, which can fire
    # dozens of recordings per user per day. Debouncing coalesces these into
    # a single Claude call per CLAUDE_DEBOUNCE_SECONDS window.
    try:
        from app.jobs.analysis import enqueue_analysis_for_recording

        scheduled = enqueue_analysis_for_recording(
            user_id=user_id, recording_id=recording_id, debounce=True,
        )
        supabase.table("recordings").update(
            {
                "celery_task_id": scheduled.get("task_id"),
                "processing_status": scheduled["processing_status"],
            }
        ).eq("id", recording_id).execute()
        processing_status = scheduled["processing_status"]
    except Exception:
        # Job broker unavailable — leave status as pending
        processing_status = "pending"

    return VoiceUploadResponse(
        recording_id=uuid.UUID(recording_id),
        storage_path=storage_path,
        original_filename=original_filename,
        file_size_bytes=file_size,
        detected_mime=validation.detected_mime,
        processing_status=processing_status,
        message="Voice recording uploaded. Analysis job queued.",
    )


@router.get(
    "/voice/check-duplicate",
    summary="Check if a voice recording already exists",
    description="Query by SHA-256 hash and/or Omi device ID to detect duplicates before upload.",
)
async def check_duplicate(
    current_user: Annotated[dict, Depends(get_current_active_user)],
    sha256: str | None = None,
    omi_id: str | None = None,
) -> dict:
    user_id = str(current_user.id)
    supabase = get_supabase()

    query = supabase.table("recordings").select("id").eq("user_id", user_id)

    if sha256:
        query = query.eq("sha256", sha256)
    if omi_id:
        query = query.eq("omi_recording_id", omi_id)

    if not sha256 and not omi_id:
        return {"is_duplicate": False}

    result = query.limit(1).execute()
    return {"is_duplicate": len(result.data) > 0}


@router.patch(
    "/voice/{recording_id}/acoustic",
    summary="Attach acoustic metadata to a recording",
    description="PATCH endpoint to update acoustic_metadata on an existing recording.",
)
async def patch_acoustic_metadata(
    recording_id: uuid.UUID,
    acoustic_metadata: dict,
    current_user: Annotated[dict, Depends(get_current_active_user)],
) -> dict:
    user_id = str(current_user.id)
    supabase = get_supabase()

    # Verify ownership
    existing = supabase.table("recordings").select("id").eq("id", str(recording_id)).eq(
        "user_id", user_id
    ).single().execute()

    if not existing.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recording not found or access denied",
        )

    supabase.table("recordings").update(
        {"acoustic_metadata": acoustic_metadata}
    ).eq("id", str(recording_id)).execute()

    return {"recording_id": str(recording_id), "updated": True}


@router.patch(
    "/voice/settings",
    summary="Update voice upload settings",
    description="Update sync settings such as sync_enabled and exclude_period.",
)
async def update_voice_settings(
    body: dict,
    current_user: Annotated[dict, Depends(get_current_active_user)],
) -> dict:
    user_id = str(current_user.id)
    supabase = get_supabase()

    allowed_keys = {"sync_enabled", "exclude_period"}
    update_payload = {k: v for k, v in body.items() if k in allowed_keys}

    if not update_payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid settings fields provided",
        )

    supabase.table("users").update(update_payload).eq("id", user_id).execute()

    return {"user_id": user_id, "updated": update_payload}
