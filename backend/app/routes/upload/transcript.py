"""
POST /api/upload/transcript — manual transcript text submission.
Links transcript to an existing recording or creates a standalone transcript record.
Triggers re-analysis if recording already exists.
"""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_active_user
from app.config import get_settings
from app.database import get_db
from app.models.audit_log import AuditLog
from app.models.recording import Recording
from app.models.user import User
from slowapi import Limiter
from slowapi.util import get_remote_address

settings = get_settings()
router = APIRouter(prefix="/api/upload", tags=["upload"])
limiter = Limiter(key_func=get_remote_address)


class TranscriptSubmitRequest(BaseModel):
    transcript: str = Field(
        ...,
        min_length=50,
        max_length=50_000,
        description="Transcript text (50–50,000 characters)",
    )
    recording_id: uuid.UUID | None = Field(
        None,
        description="Optional: link transcript to an existing recording",
    )
    source: str = Field(
        "manual",
        pattern="^(manual|omi|whisper)$",
        description="Transcript source: manual, omi, or whisper",
    )


class TranscriptSubmitResponse(BaseModel):
    recording_id: uuid.UUID
    transcript_length: int
    source: str
    processing_status: str
    message: str


@router.post(
    "/transcript",
    response_model=TranscriptSubmitResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit a manual transcript",
    description=(
        "Submit a text transcript, optionally linking it to an existing recording. "
        "Triggers async personality analysis."
    ),
)
@limiter.limit(settings.RATE_LIMIT_UPLOADS)
async def upload_transcript(
    request: Request,
    body: TranscriptSubmitRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TranscriptSubmitResponse:
    recording: Recording | None = None

    if body.recording_id:
        # Link to existing recording — verify ownership
        result = await db.execute(
            select(Recording).where(
                Recording.id == body.recording_id,
                Recording.user_id == current_user.id,
            )
        )
        recording = result.scalar_one_or_none()
        if recording is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recording not found or access denied",
            )
        recording.transcript = body.transcript
        recording.transcript_source = body.source
        recording.processing_status = "pending"
    else:
        # Create a transcript-only recording (no audio file)
        recording = Recording(
            user_id=current_user.id,
            s3_key="",
            s3_bucket="",
            original_filename="transcript.txt",
            file_size_bytes=len(body.transcript.encode("utf-8")),
            mime_type="text/plain",
            transcript=body.transcript,
            transcript_source=body.source,
            processing_status="pending",
        )
        db.add(recording)

    await db.flush()

    # Audit log
    log = AuditLog(
        user_id=current_user.id,
        event_type="upload.transcript",
        resource_type="recording",
        resource_id=str(recording.id),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        request_path=str(request.url.path),
        request_method="POST",
        response_status=202,
        metadata={
            "transcript_length": len(body.transcript),
            "source": body.source,
            "recording_id": str(recording.id),
        },
    )
    db.add(log)
    await db.flush()

    # Trigger async Celery analysis
    try:
        from app.jobs.analysis import analyze_recording_task

        task = analyze_recording_task.delay(str(recording.id))
        recording.celery_task_id = task.id
        recording.processing_status = "queued"
    except Exception:
        recording.processing_status = "pending"

    return TranscriptSubmitResponse(
        recording_id=recording.id,
        transcript_length=len(body.transcript),
        source=body.source,
        processing_status=recording.processing_status,
        message="Transcript submitted. Personality analysis queued.",
    )
