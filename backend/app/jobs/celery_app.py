"""
Celery application factory.
Workers process acoustic extraction and Claude AI analysis tasks.
"""
from celery import Celery
from kombu import Queue

from app.config import get_settings

settings = get_settings()


def create_celery_app() -> Celery:
    app = Celery(
        "character_websites",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
    )

    app.conf.update(
        # ── Serialization ─────────────────────────────────────────────────
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        # ── Timezone ──────────────────────────────────────────────────────
        timezone="UTC",
        enable_utc=True,
        # ── Task settings ─────────────────────────────────────────────────
        task_track_started=True,
        task_acks_late=True,  # ack after completion, not on receipt
        worker_prefetch_multiplier=1,  # one task at a time per worker
        task_reject_on_worker_lost=True,
        # ── Result expiry ─────────────────────────────────────────────────
        result_expires=86400,  # 24 hours
        # ── Queues ────────────────────────────────────────────────────────
        task_queues=(
            Queue("analysis", routing_key="analysis"),
            Queue("webhooks", routing_key="webhooks"),
            Queue("default", routing_key="default"),
        ),
        task_default_queue="default",
        task_routes={
            "app.jobs.analysis.analyze_recording_task": {"queue": "analysis"},
            "app.jobs.analysis.process_user_pending_analysis_task": {"queue": "analysis"},
            "app.jobs.analysis.trigger_isr_webhook_task": {"queue": "webhooks"},
            "app.jobs.monitoring.check_sync_health_task": {"queue": "default"},
        },
        # ── Retry policy ──────────────────────────────────────────────────
        task_max_retries=3,
        task_retry_backoff=True,
        task_retry_backoff_max=600,  # 10 minutes max
        task_retry_jitter=True,
        # ── Beat schedule ─────────────────────────────────────────────────
        # Beat must be started explicitly: `celery -A app.jobs.celery_app beat`.
        # Disable per-environment by setting MONITORING_ENABLED=false.
        beat_schedule={
            "sync-health-check": {
                "task": "app.jobs.monitoring.check_sync_health_task",
                "schedule": float(settings.MONITORING_BEAT_INTERVAL_SECONDS),
                "options": {"queue": "default"},
            },
        } if settings.MONITORING_ENABLED else {},
        # ── Autodiscovery ─────────────────────────────────────────────────
        include=["app.jobs.analysis", "app.jobs.monitoring"],
    )

    return app


celery_app = create_celery_app()
