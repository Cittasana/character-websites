"""
User model — stores account credentials and profile metadata.
Password is stored as bcrypt hash; never stored in plaintext.
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    subdomain: Mapped[str | None] = mapped_column(
        String(63), unique=True, nullable=True, index=True
    )
    plan: Mapped[str] = mapped_column(String(50), default="free", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ── Relationships ─────────────────────────────────────────────────────
    recordings: Mapped[list["Recording"]] = relationship(  # noqa: F821
        "Recording", back_populates="user", cascade="all, delete-orphan"
    )
    photos: Mapped[list["Photo"]] = relationship(  # noqa: F821
        "Photo", back_populates="user", cascade="all, delete-orphan"
    )
    personality_schemas: Mapped[list["PersonalitySchema"]] = relationship(  # noqa: F821
        "PersonalitySchema", back_populates="user", cascade="all, delete-orphan"
    )
    website_configs: Mapped[list["WebsiteConfig"]] = relationship(  # noqa: F821
        "WebsiteConfig", back_populates="user", cascade="all, delete-orphan"
    )
    voice_clips: Mapped[list["VoiceClip"]] = relationship(  # noqa: F821
        "VoiceClip", back_populates="user", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(  # noqa: F821
        "AuditLog", back_populates="user", cascade="all, delete-orphan"
    )
