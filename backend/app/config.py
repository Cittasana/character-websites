"""
Application configuration — all secrets loaded from environment variables.
Never hardcode credentials here.
"""
from functools import lru_cache
from typing import List, Optional

from pydantic import AnyUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── App ────────────────────────────────────────────────────────────────
    APP_ENV: str = "development"
    APP_NAME: str = "Character-Websites API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    # ── Database ───────────────────────────────────────────────────────────
    DATABASE_URL: str  # postgresql+asyncpg://user:pass@host:5432/dbname
    DATABASE_URL_SYNC: str  # postgresql://user:pass@host:5432/dbname (for Alembic)
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30

    # ── Auth ───────────────────────────────────────────────────────────────
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # ── Redis ──────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    CACHE_TTL_SECONDS: int = 3600  # 1 hour default

    # ── S3 / Object Storage ────────────────────────────────────────────────
    S3_BUCKET_NAME: str
    S3_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    S3_ENDPOINT_URL: Optional[str] = None  # for non-AWS S3-compatible stores
    S3_SIGNED_URL_EXPIRY: int = 3600  # 1 hour

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

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_db_url(cls, v: str) -> str:
        if not v.startswith(("postgresql", "asyncpg")):
            raise ValueError("DATABASE_URL must be a PostgreSQL connection string")
        return v

    @property
    def voice_max_bytes(self) -> int:
        return self.VOICE_MAX_SIZE_MB * 1024 * 1024

    @property
    def photo_max_bytes(self) -> int:
        return self.PHOTO_MAX_SIZE_MB * 1024 * 1024


@lru_cache()
def get_settings() -> Settings:
    return Settings()
