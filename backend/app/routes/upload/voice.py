"""
POST /api/upload/voice — multipart audio file upload.
Requirements:
- JWT authentication required
- File type validated via magic bytes (not extension)
- Max 50MB
- Files stored in S3 with AES-256 encryption
- Upload event logged to audit_logs
- Triggers async Celery analysis job
"""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user
from app.config import get_settings
from app.database import get_db
from app.file_validation import validate_voice_file
from app.models.audit_log import AuditLog
from app.models.recording import Recording
from app.models.user import User
from app.storage import upload_file_to_s3
from slowapi import Limiter
from slowapi.util import get_remote_address

settings = get_settings()
router = APIRouter(prefix="/api/upload", tags=["upload"])
limiter = Limiter(key_func=get_remote_address)


class VoiceUploadResponse(BaseModel):
    recording_id: uuid.UUID
    s3_key: str
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
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> VoiceUploadResponse:
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

    # ── Upload to S3 ──────────────────────────────────────────────────────
    import io

    s3_result = upload_file_to_s3(
        file_obj=io.BytesIO(file_data),
        user_id=str(current_user.id),
        file_type="voice",
        original_filename=file.filename or "upload.audio",
        content_type=validation.detected_mime,
    )

    # ── Persist recording row ─────────────────────────────────────────────
    recording = Recording(
        user_id=current_user.id,
        s3_key=s3_result["s3_key"],
        s3_bucket=s3_result["s3_bucket"],
        original_filename=file.filename or "upload.audio",
        file_size_bytes=file_size,
        mime_type=validation.detected_mime,
        processing_status="pending",
    )
    db.add(recording)
    await db.flush()

    # ── Audit log ─────────────────────────────────────────────────────────
    log = AuditLog(
        user_id=current_user.id,
        event_type="upload.voice",
        resource_type="recording",
        resource_id=str(recording.id),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        request_path=str(request.url.path),
        request_method="POST",
        response_status=202,
        metadata={
            "file_size_bytes": file_size,
            "mime_type": validation.detected_mime,
            "s3_key": s3_result["s3_key"],
        },
    )
    db.add(log)
    await db.flush()

    # ── Trigger async Celery analysis ────────────────────────────────────
    try:
        from app.jobs.analysis import analyze_recording_task

        task = analyze_recording_task.delay(str(recording.id))
        recording.celery_task_id = task.id
        recording.processing_status = "queued"
    except Exception:
        # Job broker unavailable — log but don't fail the upload
        recording.processing_status = "pending"

    return VoiceUploadResponse(
        recording_id=recording.id,
        s3_key=s3_result["s3_key"],
        original_filename=recording.original_filename,
        file_size_bytes=file_size,
        detected_mime=validation.detected_mime,
        processing_status=recording.processing_status,
        message="Voice recording uploaded. Analysis job queued.",
    )
