"""
Omi integration configuration — all secrets loaded from environment variables.
Never hardcode credentials here.

Omi uses Firebase for user auth, and its own OAuth 2.0 for third-party app authorization.
The Omi REST API base URL is: https://api.omi.me (production)
"""
from functools import lru_cache
from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class OmiSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Omi OAuth App Credentials ─────────────────────────────────────────
    # Register your app at https://developers.omi.me and get these credentials
    OMI_APP_ID: str = ""                        # Omi App ID (from developer portal)
    OMI_CLIENT_ID: str = ""                     # OAuth 2.0 Client ID
    OMI_CLIENT_SECRET: str = ""                 # OAuth 2.0 Client Secret

    # ── Omi API ───────────────────────────────────────────────────────────
    OMI_API_BASE_URL: str = "https://api.omi.me"
    OMI_AUTH_BASE_URL: str = "https://api.omi.me/v1/auth"
    OMI_OAUTH_AUTHORIZE_URL: str = "https://api.omi.me/v1/oauth/authorize"
    OMI_OAUTH_TOKEN_URL: str = "https://api.omi.me/v1/oauth/token"
    OMI_OAUTH_SCOPES: str = "memories:read conversations:read speech_profile:read"

    # OAuth redirect URI — must be registered in the Omi developer portal
    OMI_OAUTH_REDIRECT_URI: str = "http://localhost:8000/api/omi/callback"

    # ── Backend API ───────────────────────────────────────────────────────
    BACKEND_API_URL: str = "http://localhost:8000"
    BACKEND_JWT_SECRET: str = ""                # Service-to-service JWT for backend calls
    BACKEND_UPLOAD_VOICE_ENDPOINT: str = "/api/upload/voice"

    # ── Encryption ────────────────────────────────────────────────────────
    # Fernet key for encrypting temp audio buffers on disk
    # Generate with: from cryptography.fernet import Fernet; Fernet.generate_key()
    TEMP_BUFFER_ENCRYPTION_KEY: str = ""        # Base64-encoded Fernet key

    # ── Sync ──────────────────────────────────────────────────────────────
    SYNC_POLL_INTERVAL_SECONDS: int = 300       # 5 minutes
    SYNC_MAX_RECORDINGS_PER_POLL: int = 50
    SYNC_RETRY_MAX_ATTEMPTS: int = 5
    SYNC_RETRY_BASE_DELAY_SECONDS: float = 2.0

    # ── Whisper Transcription Fallback ────────────────────────────────────
    OPENAI_API_KEY: str = ""
    WHISPER_MODEL: str = "whisper-1"            # OpenAI Whisper API model
    WHISPER_LOCAL_MODEL: str = "base"           # local openai-whisper model size
    WHISPER_USE_LOCAL: bool = False             # True = use local whisper, False = use OpenAI API

    # ── Queue ─────────────────────────────────────────────────────────────
    OFFLINE_QUEUE_PATH: str = "/tmp/omi_offline_queue"
    OFFLINE_QUEUE_MAX_SIZE: int = 500           # max queued recordings

    # ── Logging ───────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"

    @field_validator("OMI_API_BASE_URL")
    @classmethod
    def strip_trailing_slash(cls, v: str) -> str:
        return v.rstrip("/")

    @property
    def voice_upload_url(self) -> str:
        return f"{self.BACKEND_API_URL}{self.BACKEND_UPLOAD_VOICE_ENDPOINT}"

    @property
    def conversations_url(self) -> str:
        return f"{self.OMI_API_BASE_URL}/v1/conversations"

    @property
    def fernet_key(self) -> Optional[bytes]:
        if self.TEMP_BUFFER_ENCRYPTION_KEY:
            return self.TEMP_BUFFER_ENCRYPTION_KEY.encode()
        return None


@lru_cache()
def get_settings() -> OmiSettings:
    return OmiSettings()
