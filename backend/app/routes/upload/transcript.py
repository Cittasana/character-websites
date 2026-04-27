"""
POST /api/upload/transcript — manual transcript text submission.
Links transcript to an existing recording or creates a standalone transcript record.
Triggers re-analysis if recording already exists.
"""
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.auth.dependencies import get_current_active_user
from app.config import get_settings
from app.supabase_client import get_supabase

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
    current_user: Annotated[dict, Depends(get_current_active_user)],
) -> TranscriptSubmitResponse:
    user_id = str(current_user.id)
    supabase = get_supabase()
    recording_id: str

    if body.recording_id:
        # Link to existing recording — verify ownership
        existing = supabase.table("recordings").select("id").eq(
            "id", str(body.recording_id)
        ).eq("user_id", user_id).single().execute()

        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recording not found or access denied",
            )

        supabase.table("recordings").update(
            {
                "transcript": body.transcript,
                "transcript_source": body.source,
                "processing_status": "pending",
            }
        ).eq("id", str(body.recording_id)).execute()

        recording_id = str(body.recording_id)
    else:
        # Create a transcript-only recording (no audio file)
        result = supabase.table("recordings").insert(
            {
                "user_id": user_id,
                "storage_path": "",
                "storage_bucket": "",
                "original_filename": "transcript.txt",
                "file_size_bytes": len(body.transcript.encode("utf-8")),
                "mime_type": "text/plain",
                "transcript": body.transcript,
                "transcript_source": body.source,
                "processing_status": "pending",
            }
        ).execute()
        recording_id = result.data[0]["id"]

    # Audit log
    try:
        supabase.table("audit_logs").insert(
            {
                "user_id": user_id,
                "event_type": "upload.transcript",
                "resource_type": "recording",
                "resource_id": recording_id,
                "ip_address": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
                "request_path": str(request.url.path),
                "request_method": "POST",
                "response_status": 202,
                "metadata": {
                    "transcript_length": len(body.transcript),
                    "source": body.source,
                    "recording_id": recording_id,
                },
            }
        ).execute()
    except Exception:
        pass

    # Trigger Celery analysis. Omi-sourced transcripts go through the
    # debouncer (Omi can deliver many short transcripts per hour); manual
    # paste runs immediately so the user sees a fresh website right away.
    # Quota and global Anthropic-RPM apply in both paths.
    processing_status = "pending"
    try:
        from app.jobs.analysis import enqueue_analysis_for_recording

        scheduled = enqueue_analysis_for_recording(
            user_id=user_id,
            recording_id=recording_id,
            debounce=(body.source == "omi"),
        )
        supabase.table("recordings").update(
            {
                "celery_task_id": scheduled.get("task_id"),
                "processing_status": scheduled["processing_status"],
            }
        ).eq("id", recording_id).execute()
        processing_status = scheduled["processing_status"]
    except Exception:
        processing_status = "pending"

    return TranscriptSubmitResponse(
        recording_id=uuid.UUID(recording_id),
        transcript_length=len(body.transcript),
        source=body.source,
        processing_status=processing_status,
        message="Transcript submitted. Personality analysis queued.",
    )
