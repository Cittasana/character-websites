"""
Application configuration — all secrets loaded from environment variables.
Never hardcode credentials here.
"""
from functools import lru_cache
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env.local",
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

    @property
    def voice_max_bytes(self) -> int:
        return self.VOICE_MAX_SIZE_MB * 1024 * 1024

    @property
    def photo_max_bytes(self) -> int:
        return self.PHOTO_MAX_SIZE_MB * 1024 * 1024


@lru_cache()
def get_settings() -> Settings:
    return Settings()
