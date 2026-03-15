"""
Celery tasks for the analysis pipeline:
1. analyze_recording_task — acoustic extraction + Claude personality analysis
2. trigger_isr_webhook_task — notify Next.js ISR endpoint to re-render
"""
import asyncio
import logging
import uuid
from typing import Any

import httpx
from celery import Task
from sqlalchemy import select

from app.analysis.acoustic import extract_acoustic_metadata, format_acoustic_for_claude
from app.analysis.claude_analysis import analyze_personality_with_claude
from app.config import get_settings
from app.database import get_db_context
from app.jobs.celery_app import celery_app
from app.models.personality_schema import PersonalitySchema
from app.models.recording import Recording
from app.models.website_config import WebsiteConfig

settings = get_settings()
logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run an async coroutine in a new event loop (for Celery worker context)."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(
    bind=True,
    name="app.jobs.analysis.analyze_recording_task",
    max_retries=3,
    default_retry_delay=30,
    queue="analysis",
    acks_late=True,
)
def analyze_recording_task(self: Task, recording_id: str) -> dict[str, Any]:
    """
    Main analysis pipeline task.
    1. Load recording from DB
    2. Extract acoustic metadata (if audio file exists)
    3. Run Claude personality analysis
    4. Store versioned PersonalitySchema
    5. Create/update WebsiteConfig
    6. Trigger ISR webhook
    """
    logger.info("Starting analysis for recording_id=%s", recording_id)

    try:
        result = _run_async(_analyze_recording_async(recording_id, self))
        logger.info("Analysis complete for recording_id=%s", recording_id)
        return result
    except Exception as exc:
        logger.error("Analysis failed for recording_id=%s: %s", recording_id, exc, exc_info=True)
        # Mark recording as failed in DB
        _run_async(_mark_recording_failed(recording_id, str(exc)))
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=30 * (2 ** self.request.retries))


async def _analyze_recording_async(recording_id: str, task: Task) -> dict[str, Any]:
    """Async implementation of the analysis pipeline."""
    async with get_db_context() as db:
        # ── Load recording ────────────────────────────────────────────────
        result = await db.execute(
            select(Recording).where(Recording.id == uuid.UUID(recording_id))
        )
        recording = result.scalar_one_or_none()
        if recording is None:
            raise ValueError(f"Recording {recording_id} not found")

        recording.processing_status = "processing"
        await db.flush()

        # ── Acoustic extraction (skip if transcript-only) ─────────────────
        acoustic_metadata: dict[str, Any] = {}
        acoustic_summary = "No audio file available — transcript-only analysis."

        if recording.s3_key and recording.s3_key != "":
            try:
                audio_bytes = await _download_from_s3(recording.s3_key, recording.s3_bucket)
                acoustic_metadata = extract_acoustic_metadata(audio_bytes)
                acoustic_summary = format_acoustic_for_claude(acoustic_metadata)
                recording.acoustic_metadata = acoustic_metadata
                if acoustic_metadata.get("duration_seconds"):
                    recording.duration_seconds = acoustic_metadata["duration_seconds"]
            except Exception as exc:
                logger.warning("Acoustic extraction failed (non-fatal): %s", exc)
                acoustic_summary = f"Acoustic analysis failed: {exc}"

        # ── Claude analysis ───────────────────────────────────────────────
        transcript = recording.transcript or ""
        if not transcript.strip():
            raise ValueError("Recording has no transcript — cannot run personality analysis")

        schema_data, raw_response = await analyze_personality_with_claude(
            transcript=transcript,
            acoustic_summary=acoustic_summary,
        )

        # ── Get next version number ───────────────────────────────────────
        existing = await db.execute(
            select(PersonalitySchema)
            .where(
                PersonalitySchema.user_id == recording.user_id,
                PersonalitySchema.is_current == True,  # noqa: E712
            )
        )
        existing_schemas = existing.scalars().all()
        next_version = max((s.version for s in existing_schemas), default=0) + 1

        # Mark old schemas as not current
        for old_schema in existing_schemas:
            old_schema.is_current = False

        # ── Store personality schema ──────────────────────────────────────
        personality_schema = PersonalitySchema(
            user_id=recording.user_id,
            recording_id=recording.id,
            version=next_version,
            is_current=True,
            claude_model=settings.CLAUDE_MODEL,
            dimensions=schema_data["dimensions"],
            persona_blend=schema_data["persona_blend"],
            color_palette=schema_data["color_palette"],
            typography=schema_data["typography"],
            layout=schema_data["layout"],
            animation=schema_data["animation"],
            cv_content=schema_data.get("cv_content"),
            dating_content=schema_data.get("dating_content"),
            raw_claude_response=raw_response,
        )
        db.add(personality_schema)
        await db.flush()

        # ── Create/update website config ──────────────────────────────────
        wc_result = await db.execute(
            select(WebsiteConfig).where(
                WebsiteConfig.user_id == recording.user_id
            ).order_by(WebsiteConfig.created_at.desc()).limit(1)
        )
        website_config = wc_result.scalar_one_or_none()

        if website_config is None:
            website_config = WebsiteConfig(
                user_id=recording.user_id,
                personality_schema_id=personality_schema.id,
                version=1,
                config=_build_website_config(schema_data),
                site_mode="cv",
            )
            db.add(website_config)
        else:
            website_config.personality_schema_id = personality_schema.id
            website_config.version += 1
            website_config.config = _build_website_config(schema_data)
            website_config.render_webhook_status = "pending"

        # ── Mark recording as complete ────────────────────────────────────
        recording.processing_status = "completed"
        await db.flush()

        user_id = str(recording.user_id)
        schema_id = str(personality_schema.id)

    # ── Trigger ISR webhook (outside DB transaction) ──────────────────────
    trigger_isr_webhook_task.delay(user_id=user_id, schema_id=schema_id)

    return {
        "recording_id": recording_id,
        "personality_schema_id": schema_id,
        "user_id": user_id,
        "version": next_version,
    }


async def _download_from_s3(s3_key: str, bucket: str) -> bytes:
    """Download audio file bytes from S3 for acoustic analysis."""
    import boto3

    client = boto3.client(
        "s3",
        region_name=settings.S3_REGION,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        **({"endpoint_url": settings.S3_ENDPOINT_URL} if settings.S3_ENDPOINT_URL else {}),
    )

    import io

    buffer = io.BytesIO()
    client.download_fileobj(bucket, s3_key, buffer)
    return buffer.getvalue()


async def _mark_recording_failed(recording_id: str, error_msg: str) -> None:
    """Mark a recording as failed in the database."""
    async with get_db_context() as db:
        result = await db.execute(
            select(Recording).where(Recording.id == uuid.UUID(recording_id))
        )
        recording = result.scalar_one_or_none()
        if recording:
            recording.processing_status = "failed"
            recording.error_message = error_msg[:1000]


def _build_website_config(schema_data: dict[str, Any]) -> dict[str, Any]:
    """
    Build the full website configuration object from a personality schema.
    This is the payload the Next.js frontend consumes.
    """
    return {
        "theme": {
            "color_palette": schema_data["color_palette"],
            "typography": schema_data["typography"],
            "animation": schema_data["animation"],
        },
        "layout": schema_data["layout"],
        "persona": schema_data["persona_blend"],
        "dimensions": schema_data["dimensions"],
        "sections": {
            "cv": schema_data.get("cv_content", {}),
            "dating": schema_data.get("dating_content", {}),
        },
        "generated_at": _utc_now_iso(),
    }


def _utc_now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(tz=timezone.utc).isoformat()


@celery_app.task(
    bind=True,
    name="app.jobs.analysis.trigger_isr_webhook_task",
    max_retries=5,
    default_retry_delay=10,
    queue="webhooks",
)
def trigger_isr_webhook_task(
    self: Task,
    user_id: str,
    schema_id: str,
) -> dict[str, Any]:
    """
    Notify the Next.js frontend ISR endpoint to revalidate the user's website.
    """
    webhook_url = settings.FRONTEND_ISR_WEBHOOK_URL
    webhook_secret = settings.FRONTEND_ISR_WEBHOOK_SECRET

    if not webhook_url:
        logger.info("ISR webhook URL not configured — skipping")
        return {"skipped": True}

    try:
        with httpx.Client(timeout=10.0) as client:
            headers = {}
            if webhook_secret:
                headers["X-Webhook-Secret"] = webhook_secret

            response = client.post(
                webhook_url,
                json={"user_id": user_id, "schema_id": schema_id},
                headers=headers,
            )
            response.raise_for_status()

        logger.info(
            "ISR webhook triggered for user=%s schema=%s status=%s",
            user_id, schema_id, response.status_code,
        )
        return {"status": "ok", "http_status": response.status_code}

    except Exception as exc:
        logger.error("ISR webhook failed: %s", exc)
        raise self.retry(exc=exc)
