"""
Celery tasks for the analysis pipeline:
1. analyze_recording_task — acoustic extraction + Claude personality analysis
2. trigger_isr_webhook_task — notify Next.js ISR endpoint to re-render
"""
import logging
from datetime import datetime, timezone
from typing import Any

import httpx
from celery import Task

from app.analysis.acoustic import extract_acoustic_metadata, format_acoustic_for_claude
from app.analysis.claude_analysis import analyze_personality_with_claude
from app.config import get_settings
from app.jobs.celery_app import celery_app
from app.supabase_client import get_supabase

settings = get_settings()
logger = logging.getLogger(__name__)


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
    1. Load recording from Supabase DB
    2. Download audio from Supabase Storage and extract acoustic metadata
    3. Run Claude personality analysis
    4. Store versioned PersonalitySchema
    5. Create/update WebsiteConfig
    6. Trigger ISR webhook
    """
    logger.info("Starting analysis for recording_id=%s", recording_id)

    try:
        result = _analyze_recording(recording_id)
        logger.info("Analysis complete for recording_id=%s", recording_id)
        return result
    except Exception as exc:
        logger.error("Analysis failed for recording_id=%s: %s", recording_id, exc, exc_info=True)
        _mark_recording_failed(recording_id, str(exc))
        raise self.retry(exc=exc, countdown=30 * (2 ** self.request.retries))


def _analyze_recording(recording_id: str) -> dict[str, Any]:
    """Synchronous implementation of the analysis pipeline."""
    supabase = get_supabase()

    # ── Load recording ────────────────────────────────────────────────────
    rec_result = supabase.table("recordings").select("*").eq(
        "id", recording_id
    ).single().execute()

    if not rec_result.data:
        raise ValueError(f"Recording {recording_id} not found")

    recording = rec_result.data

    # Mark as processing
    supabase.table("recordings").update(
        {"processing_status": "processing"}
    ).eq("id", recording_id).execute()

    # ── Acoustic extraction (skip if transcript-only) ─────────────────────
    acoustic_metadata: dict[str, Any] = {}
    acoustic_summary = "No audio file available — transcript-only analysis."
    storage_path = recording.get("storage_path", "")

    if storage_path:
        try:
            audio_bytes = supabase.storage.from_(
                recording.get("storage_bucket", "voice-recordings")
            ).download(storage_path)

            acoustic_metadata = extract_acoustic_metadata(audio_bytes)
            acoustic_summary = format_acoustic_for_claude(acoustic_metadata)

            update_payload: dict[str, Any] = {"acoustic_metadata": acoustic_metadata}
            if acoustic_metadata.get("duration_seconds"):
                update_payload["duration_seconds"] = acoustic_metadata["duration_seconds"]

            supabase.table("recordings").update(update_payload).eq(
                "id", recording_id
            ).execute()
        except Exception as exc:
            logger.warning("Acoustic extraction failed (non-fatal): %s", exc)
            acoustic_summary = f"Acoustic analysis failed: {exc}"

    # ── Claude analysis ───────────────────────────────────────────────────
    import asyncio

    transcript = recording.get("transcript", "") or ""
    if not transcript.strip():
        raise ValueError("Recording has no transcript — cannot run personality analysis")

    loop = asyncio.new_event_loop()
    try:
        schema_data, raw_response = loop.run_until_complete(
            analyze_personality_with_claude(
                transcript=transcript,
                acoustic_summary=acoustic_summary,
            )
        )
    finally:
        loop.close()

    user_id = recording["user_id"]

    # ── Get next version number ───────────────────────────────────────────
    existing_result = supabase.table("personality_schemas").select(
        "id, version"
    ).eq("user_id", user_id).eq("is_current", True).execute()

    existing_schemas = existing_result.data or []
    next_version = max((s["version"] for s in existing_schemas), default=0) + 1

    # Mark old schemas as not current
    if existing_schemas:
        old_ids = [s["id"] for s in existing_schemas]
        supabase.table("personality_schemas").update(
            {"is_current": False}
        ).in_("id", old_ids).execute()

    # ── Store personality schema ──────────────────────────────────────────
    now_iso = datetime.now(tz=timezone.utc).isoformat()
    schema_insert = {
        "user_id": user_id,
        "recording_id": recording_id,
        "version": next_version,
        "is_current": True,
        "claude_model": settings.CLAUDE_MODEL,
        "dimensions": schema_data["dimensions"],
        "persona_blend": schema_data["persona_blend"],
        "color_palette": schema_data["color_palette"],
        "typography": schema_data["typography"],
        "layout": schema_data["layout"],
        "animation": schema_data["animation"],
        "cv_content": schema_data.get("cv_content"),
        "dating_content": schema_data.get("dating_content"),
        "raw_claude_response": raw_response,
    }

    schema_result = supabase.table("personality_schemas").insert(schema_insert).execute()
    new_schema_id = schema_result.data[0]["id"]

    # ── Create/update website config ──────────────────────────────────────
    wc_result = supabase.table("website_configs").select("id, version").eq(
        "user_id", user_id
    ).order("created_at", desc=True).limit(1).execute()

    wc_data = wc_result.data[0] if wc_result.data else None

    if wc_data is None:
        supabase.table("website_configs").insert(
            {
                "user_id": user_id,
                "personality_schema_id": new_schema_id,
                "version": 1,
                "config": _build_website_config(schema_data),
                "site_mode": "cv",
                "is_published": False,
            }
        ).execute()
    else:
        supabase.table("website_configs").update(
            {
                "personality_schema_id": new_schema_id,
                "version": wc_data["version"] + 1,
                "config": _build_website_config(schema_data),
                "render_webhook_status": "pending",
            }
        ).eq("id", wc_data["id"]).execute()

    # ── Mark recording as complete ────────────────────────────────────────
    supabase.table("recordings").update(
        {"processing_status": "completed"}
    ).eq("id", recording_id).execute()

    # ── Audit log ─────────────────────────────────────────────────────────
    try:
        supabase.table("audit_logs").insert(
            {
                "user_id": user_id,
                "event_type": "analysis_complete",
                "resource_type": "recording",
                "resource_id": recording_id,
                "metadata": {
                    "personality_schema_id": new_schema_id,
                    "version": next_version,
                },
            }
        ).execute()
    except Exception:
        pass

    # ── Trigger ISR webhook ───────────────────────────────────────────────
    trigger_isr_webhook_task.delay(user_id=user_id, schema_id=new_schema_id)

    return {
        "recording_id": recording_id,
        "personality_schema_id": new_schema_id,
        "user_id": user_id,
        "version": next_version,
    }


def _mark_recording_failed(recording_id: str, error_msg: str) -> None:
    """Mark a recording as failed in the database."""
    try:
        supabase = get_supabase()
        supabase.table("recordings").update(
            {
                "processing_status": "failed",
                "error_message": error_msg[:1000],
            }
        ).eq("id", recording_id).execute()
    except Exception as exc:
        logger.error("Could not mark recording %s as failed: %s", recording_id, exc)


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
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
    }


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
