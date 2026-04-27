"""
Celery tasks for the analysis pipeline:
1. analyze_recording_task — acoustic extraction + Claude personality analysis
2. process_user_pending_analysis_task — debounced entry point used by Omi sync
3. trigger_isr_webhook_task — notify Next.js ISR endpoint to re-render
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
from app.jobs.rate_limiter import (
    acquire_global_token,
    clear_scheduled_marker,
    consume_user_quota,
    mark_user_pending,
    refund_user_quota,
    seconds_until_utc_midnight,
    take_user_pending,
    try_schedule_user_analysis,
)
from app.supabase_client import get_supabase

settings = get_settings()
logger = logging.getLogger(__name__)


# ── Public scheduling entry point ─────────────────────────────────────────────

def enqueue_analysis_for_recording(
    user_id: str,
    recording_id: str,
    *,
    debounce: bool = True,
) -> dict[str, Any]:
    """
    Trigger Claude analysis for a freshly inserted recording.

    Args:
        user_id: Owner of the recording.
        recording_id: Newly inserted ``recordings`` row id.
        debounce: When True (Omi sync default), Claude calls for the same
            user are coalesced inside ``CLAUDE_DEBOUNCE_SECONDS``. When False
            (manual transcript paste, retries), the analysis is enqueued
            immediately — quota and global RPM still apply inside the task.

    Returns:
        Dict describing the dispatched action — see ``processing_status``
        callers expect for surfacing to the API client.
    """
    if not debounce:
        task = analyze_recording_task.delay(recording_id)
        return {
            "mode": "immediate",
            "task_id": task.id,
            "processing_status": "queued",
        }

    # Debounced path: always overwrite the pending pointer with the latest
    # recording, then schedule a Celery task only if no debounce window is
    # currently armed.
    mark_user_pending(user_id, recording_id)

    if try_schedule_user_analysis(user_id, settings.CLAUDE_DEBOUNCE_SECONDS):
        task = process_user_pending_analysis_task.apply_async(
            args=[user_id],
            countdown=settings.CLAUDE_DEBOUNCE_SECONDS,
        )
        logger.info(
            "Scheduled debounced Claude analysis for user=%s recording=%s in %ss "
            "(task_id=%s)",
            user_id[:8], recording_id, settings.CLAUDE_DEBOUNCE_SECONDS, task.id,
        )
        return {
            "mode": "debounced",
            "task_id": task.id,
            "processing_status": "queued_debounced",
        }

    logger.info(
        "Coalesced Claude analysis for user=%s recording=%s into existing debounce window",
        user_id[:8], recording_id,
    )
    return {
        "mode": "coalesced",
        "task_id": None,
        "processing_status": "queued_debounced",
    }


# ── Debounced entry task (Omi-burst friendly) ────────────────────────────────

@celery_app.task(
    bind=True,
    name="app.jobs.analysis.process_user_pending_analysis_task",
    max_retries=3,
    default_retry_delay=60,
    queue="analysis",
    acks_late=True,
)
def process_user_pending_analysis_task(self: Task, user_id: str) -> dict[str, Any]:
    """
    Fires after ``CLAUDE_DEBOUNCE_SECONDS`` to process the *latest* pending
    recording for ``user_id``.

    Atomically pulls the pending recording_id, then routes through the same
    rate-limited path as ``analyze_recording_task``. Older Omi updates that
    arrived during the debounce window are intentionally dropped — only the
    newest transcript drives the personality refresh.
    """
    # Free the schedule marker first: any new upload during the rest of this
    # task can immediately mark a fresh pending + arm the next debounce cycle.
    clear_scheduled_marker(user_id)

    recording_id = take_user_pending(user_id)
    if not recording_id:
        logger.info(
            "Debounced analysis fired for user=%s but no pending recording — skipping",
            user_id[:8],
        )
        return {"skipped": True, "reason": "no_pending_recording"}

    logger.info(
        "Debounced analysis firing for user=%s -> recording=%s",
        user_id[:8], recording_id,
    )
    return _run_with_rate_limits(self, recording_id)


# ── Direct entry task (manual paths, queue retries) ──────────────────────────

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
    Main analysis pipeline task (no debounce).

    Use ``enqueue_analysis_for_recording`` instead of calling ``.delay()``
    directly so per-user debouncing applies for Omi-driven uploads.
    """
    logger.info("Starting analysis for recording_id=%s", recording_id)
    return _run_with_rate_limits(self, recording_id)


# ── Rate-limited execution wrapper ───────────────────────────────────────────

def _run_with_rate_limits(task: Task, recording_id: str) -> dict[str, Any]:
    """
    Shared body used by both entry tasks.

    Order of guards:
        1. Global RPM token-bucket (transient back-pressure → Celery retry).
        2. Per-user daily quota (terminal → mark recording skipped).
        3. Actual analysis pipeline.

    Quota is refunded if the analysis itself fails, so retries do not
    permanently consume a user's daily budget.
    """
    user_id = _get_recording_user_id(recording_id)
    if user_id is None:
        logger.warning(
            "Recording %s has no user_id (deleted?) — skipping analysis", recording_id,
        )
        return {"skipped": True, "reason": "recording_missing"}

    # Step 1: respect global Anthropic RPM budget.
    if not acquire_global_token(settings.CLAUDE_GLOBAL_TOKEN_TIMEOUT_SECONDS):
        backoff = min(300, 30 * (2 ** task.request.retries))
        logger.warning(
            "Global Claude RPM bucket empty — retrying recording=%s in %ss "
            "(attempt %s/%s)",
            recording_id, backoff, task.request.retries + 1, task.max_retries,
        )
        raise task.retry(countdown=backoff)

    # Step 2: per-user daily cap.
    if not consume_user_quota(user_id, settings.CLAUDE_MAX_PER_USER_PER_DAY):
        logger.warning(
            "Daily Claude quota exhausted for user=%s — recording=%s deferred",
            user_id[:8], recording_id,
        )
        _mark_recording_quota_skipped(recording_id)
        # Re-arm debounce so the recording auto-picks up after midnight UTC
        # without user intervention.
        try:
            mark_user_pending(user_id, recording_id)
            if try_schedule_user_analysis(user_id, seconds_until_utc_midnight()):
                process_user_pending_analysis_task.apply_async(
                    args=[user_id],
                    countdown=seconds_until_utc_midnight(),
                )
        except Exception as reschedule_exc:
            logger.error(
                "Could not reschedule quota-blocked recording=%s: %s",
                recording_id, reschedule_exc,
            )
        return {"skipped": True, "reason": "user_quota_exceeded", "user_id": user_id}

    # Step 3: actual pipeline.
    try:
        result = _analyze_recording(recording_id)
        logger.info("Analysis complete for recording_id=%s", recording_id)
        return result
    except Exception as exc:
        # Refund quota so a transient failure does not waste the user's budget.
        try:
            refund_user_quota(user_id)
        except Exception:
            logger.warning("Quota refund failed for user=%s (non-fatal)", user_id[:8])

        logger.error(
            "Analysis failed for recording_id=%s: %s", recording_id, exc, exc_info=True,
        )
        _mark_recording_failed(recording_id, str(exc))
        if task.request.retries >= task.max_retries:
            _notify_analysis_failure(recording_id, exc, attempts=task.request.retries + 1)
            raise
        raise task.retry(exc=exc, countdown=30 * (2 ** task.request.retries))


def _get_recording_user_id(recording_id: str) -> str | None:
    """Light query — we need user_id before running the heavy pipeline."""
    try:
        supabase = get_supabase()
        result = supabase.table("recordings").select("user_id").eq(
            "id", recording_id
        ).single().execute()
        return (result.data or {}).get("user_id")
    except Exception as exc:
        logger.error("user_id lookup failed for recording=%s: %s", recording_id, exc)
        return None


def _mark_recording_quota_skipped(recording_id: str) -> None:
    """Persist a deferred status for quota-blocked recordings."""
    try:
        supabase = get_supabase()
        supabase.table("recordings").update(
            {
                "processing_status": "deferred_quota",
                "error_message": "Daily Claude quota exceeded — auto-resumes after UTC midnight",
            }
        ).eq("id", recording_id).execute()
    except Exception as exc:
        logger.error(
            "Could not mark recording %s as quota-skipped: %s", recording_id, exc,
        )


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


def _notify_analysis_failure(
    recording_id: str, exc: BaseException, *, attempts: int
) -> None:
    """Persist + alert on a final analysis failure (after retries exhausted)."""
    try:
        from app.monitoring import AlertSeverity, get_alerter, record_analysis_failure

        user_id: str | None = None
        try:
            supabase = get_supabase()
            row = supabase.table("recordings").select("user_id").eq(
                "id", recording_id
            ).single().execute()
            user_id = (row.data or {}).get("user_id")
        except Exception:
            pass

        record_analysis_failure(
            recording_id=recording_id,
            user_id=user_id,
            error_message=str(exc),
            attempts=attempts,
        )
        get_alerter().send(
            severity=AlertSeverity.CRITICAL,
            title="Claude analysis failed (retries exhausted)",
            message=str(exc)[:500],
            context={
                "recording_id": recording_id,
                "user_id": (user_id or "")[:8],
                "attempts": attempts,
            },
            dedup_key=f"analysis:{recording_id}",
        )
    except Exception as notify_exc:
        logger.error("notify_analysis_failure failed: %s", notify_exc)


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
