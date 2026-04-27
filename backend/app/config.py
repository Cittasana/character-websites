"""
Application configuration — all secrets loaded from environment variables.
Never hardcode credentials here.
"""
from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ────────────────────────────────────────────────────────────────
    APP_ENV: str = "development"
    APP_NAME: str = "Character-Websites API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    # ── Supabase ───────────────────────────────────────────────────────────
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str

    # ── Redis ──────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    CACHE_TTL_SECONDS: int = 3600  # 1 hour default

    # ── Claude AI ─────────────────────────────────────────────────────────
    ANTHROPIC_API_KEY: str
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"
    CLAUDE_MAX_TOKENS: int = 4096

    # ── Claude Rate Limiting (Omi-Massen-Updates) ─────────────────────────
    # Debounce: Mehrere Recordings desselben Users innerhalb dieses Fensters
    # werden zu EINEM Claude-Call koalesziert. Default 600s = 10 min.
    CLAUDE_DEBOUNCE_SECONDS: int = 600
    # Hartes Cap an Claude-Analysen pro User pro UTC-Tag.
    CLAUDE_MAX_PER_USER_PER_DAY: int = 30
    # Globaler Token-Bucket: Requests-pro-Minute über alle Worker.
    # Anthropic Tier-Limits beachten (z. B. Tier 2 Sonnet ~50 RPM).
    CLAUDE_GLOBAL_RPM: int = 30
    # Maximale Wartezeit für einen globalen Token vor Re-Queue.
    CLAUDE_GLOBAL_TOKEN_TIMEOUT_SECONDS: float = 60.0

    # ── Upload Limits ──────────────────────────────────────────────────────
    VOICE_MAX_SIZE_MB: int = 50
    PHOTO_MAX_SIZE_MB: int = 10
    VOICE_ALLOWED_TYPES: List[str] = ["audio/mpeg", "audio/wav", "audio/x-m4a", "audio/mp4"]
    PHOTO_ALLOWED_TYPES: List[str] = ["image/jpeg", "image/png", "image/webp"]

    # ── Rate Limiting ──────────────────────────────────────────────────────
    RATE_LIMIT_UPLOADS: str = "100/hour"
    RATE_LIMIT_RETRIEVE: str = "1000/hour"

    # ── Frontend Webhook ──────────────────────────────────────────────────
    FRONTEND_ISR_WEBHOOK_URL: Optional[str] = None
    FRONTEND_ISR_WEBHOOK_SECRET: Optional[str] = None

    # Supabase E-Mail-Bestätigung: exakt diese URL muss unter Authentication → URL Configuration
    # in „Redirect URLs“ erlaubt sein (z. B. https://characterwebsites.vercel.app).
    AUTH_EMAIL_REDIRECT_URL: Optional[str] = None

    # ── Monitoring & Alerting ─────────────────────────────────────────────
    # Master switch. Disable in tests / local dev to silence webhook calls.
    MONITORING_ENABLED: bool = True

    # Slack/Discord-compatible incoming webhook. Empty = log-only mode.
    MONITORING_ALERT_WEBHOOK_URL: Optional[str] = None
    MONITORING_ALERT_TIMEOUT_SECONDS: float = 5.0

    # Suppress identical alerts within this window (seconds) — prevents
    # pager storms when the same failure repeats every sync cycle.
    MONITORING_ALERT_DEDUP_WINDOW_SECONDS: int = 300

    # Token gating the admin /api/monitoring/sync-health endpoint. Required.
    MONITORING_ADMIN_TOKEN: Optional[str] = None

    # Health evaluator window + thresholds (tunable per environment)
    MONITORING_SYNC_WINDOW_MINUTES: int = 60
    MONITORING_STALE_SYNC_MINUTES: int = 30
    MONITORING_FAILURE_WARN_RATE: float = 0.25  # 25% sync failures → warn
    MONITORING_FAILURE_CRIT_RATE: float = 0.50  # 50% sync failures → critical
    MONITORING_STUCK_RECORDING_MINUTES: int = 30
    MONITORING_ANALYSIS_FAILURE_CRIT: int = 5  # >=N failures in window → critical

    # Beat schedule: run the periodic health check this often
    MONITORING_BEAT_INTERVAL_SECONDS: int = 300

    @property
    def voice_max_bytes(self) -> int:
        return self.VOICE_MAX_SIZE_MB * 1024 * 1024

    @property
    def photo_max_bytes(self) -> int:
        return self.PHOTO_MAX_SIZE_MB * 1024 * 1024


@lru_cache()
def get_settings() -> Settings:
    return Settings()
