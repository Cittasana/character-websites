"""
WebsiteConfig model — the rendered website configuration for each user.
This is the output that the Next.js frontend consumes.
"""
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class WebsiteConfig(Base):
    __tablename__ = "website_configs"

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
    personality_schema_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("personality_schemas.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    subdomain: Mapped[str | None] = mapped_column(
        String(63), nullable=True, index=True
    )

    # Full website configuration object
    config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # Site mode: cv | dating | combined
    site_mode: Mapped[str] = mapped_column(
        String(50), default="cv", nullable=False
    )

    # ISR revalidation tracking
    last_rendered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    render_webhook_status: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )  # pending | triggered | success | failed

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
    user: Mapped["User"] = relationship("User", back_populates="website_configs")  # noqa: F821
    personality_schema: Mapped["PersonalitySchema"] = relationship(  # noqa: F821
        "PersonalitySchema", back_populates="website_configs"
    )
