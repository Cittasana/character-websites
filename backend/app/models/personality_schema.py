"""
PersonalitySchema model — versioned AI-generated personality analysis results.
Includes pgvector embedding column for semantic search/similarity.
"""
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

try:
    from pgvector.sqlalchemy import Vector
    PGVECTOR_AVAILABLE = True
except ImportError:
    PGVECTOR_AVAILABLE = False
    Vector = None  # type: ignore


class PersonalitySchema(Base):
    __tablename__ = "personality_schemas"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    recording_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recordings.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_current: Mapped[bool] = mapped_column(default=True, nullable=False, index=True)
    claude_model: Mapped[str] = mapped_column(String(100), nullable=False)

    # Core personality dimensions (0-100 each)
    dimensions: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    # { warmth, energy, confidence, curiosity, formality, humor, openness }

    # Persona blend
    persona_blend: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    # { primary, primary_weight, secondary, secondary_weight }

    # Design directives
    color_palette: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    typography: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    layout: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    animation: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    # Content schemas
    cv_content: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    dating_content: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Full raw Claude response
    raw_claude_response: Mapped[str | None] = mapped_column(Text, nullable=True)

    # pgvector embedding (1536 dims — OpenAI-compatible or computed from dimensions)
    # Declared dynamically to handle environments without pgvector
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
    user: Mapped["User"] = relationship("User", back_populates="personality_schemas")  # noqa: F821
    recording: Mapped["Recording"] = relationship(  # noqa: F821
        "Recording", back_populates="personality_schemas"
    )
    website_configs: Mapped[list["WebsiteConfig"]] = relationship(  # noqa: F821
        "WebsiteConfig", back_populates="personality_schema"
    )


# Dynamically add Vector column if pgvector is available
if PGVECTOR_AVAILABLE and Vector is not None:
    from sqlalchemy import Column
    PersonalitySchema.__table__.append_column(  # type: ignore
        Column("embedding", Vector(1536), nullable=True)
    )
