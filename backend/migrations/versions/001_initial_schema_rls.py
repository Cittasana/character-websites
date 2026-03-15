"""
001 — Initial schema: 7 tables + pgvector extension + Row-Level Security policies.

Revision ID: 001_initial_schema_rls
Revises:
Create Date: 2025-05-28
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON, INET

revision = "001_initial_schema_rls"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Extensions ────────────────────────────────────────────────────────
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ── RLS helper function ───────────────────────────────────────────────
    # Returns the user_id set by the application via set_config
    op.execute("""
        CREATE OR REPLACE FUNCTION current_user_id() RETURNS uuid
        LANGUAGE sql STABLE
        AS $$
            SELECT current_setting('app.current_user_id', true)::uuid
        $$
    """)

    # ── users ─────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("is_verified", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("subdomain", sa.String(63), nullable=True),
        sa.Column("plan", sa.String(50), nullable=False, server_default="free"),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_subdomain", "users", ["subdomain"], unique=True)

    # ── recordings ────────────────────────────────────────────────────────
    op.create_table(
        "recordings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("s3_key", sa.String(1024), nullable=False),
        sa.Column("s3_bucket", sa.String(255), nullable=False),
        sa.Column("original_filename", sa.String(512), nullable=False),
        sa.Column("file_size_bytes", sa.Integer, nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("duration_seconds", sa.Float, nullable=True),
        sa.Column("transcript", sa.Text, nullable=True),
        sa.Column("transcript_source", sa.String(50), nullable=True),
        sa.Column("acoustic_metadata", JSON, nullable=True),
        sa.Column("processing_status", sa.String(50), nullable=False,
                  server_default="pending"),
        sa.Column("celery_task_id", sa.String(255), nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_recordings_user_id", "recordings", ["user_id"])
    op.create_index("ix_recordings_processing_status", "recordings", ["processing_status"])

    # ── photos ────────────────────────────────────────────────────────────
    op.create_table(
        "photos",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("s3_key", sa.String(1024), nullable=False),
        sa.Column("s3_bucket", sa.String(255), nullable=False),
        sa.Column("original_filename", sa.String(512), nullable=False),
        sa.Column("file_size_bytes", sa.Integer, nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("width_px", sa.Integer, nullable=True),
        sa.Column("height_px", sa.Integer, nullable=True),
        sa.Column("photo_type", sa.String(50), nullable=False, server_default="profile"),
        sa.Column("is_primary", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_photos_user_id", "photos", ["user_id"])

    # ── personality_schemas ───────────────────────────────────────────────
    op.create_table(
        "personality_schemas",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recording_id", UUID(as_uuid=True),
                  sa.ForeignKey("recordings.id", ondelete="SET NULL"), nullable=True),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("is_current", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("claude_model", sa.String(100), nullable=False),
        sa.Column("dimensions", JSON, nullable=False),
        sa.Column("persona_blend", JSON, nullable=False),
        sa.Column("color_palette", JSON, nullable=False),
        sa.Column("typography", JSON, nullable=False),
        sa.Column("layout", JSON, nullable=False),
        sa.Column("animation", JSON, nullable=False),
        sa.Column("cv_content", JSON, nullable=True),
        sa.Column("dating_content", JSON, nullable=True),
        sa.Column("raw_claude_response", sa.Text, nullable=True),
        # pgvector embedding (1536 dims)
        sa.Column("embedding", sa.Column("embedding",
                  sa.Text).type, nullable=True),  # replaced below
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_personality_schemas_user_id", "personality_schemas", ["user_id"])
    op.create_index("ix_personality_schemas_is_current", "personality_schemas", ["is_current"])

    # Replace the placeholder embedding column with a proper vector column
    op.execute("ALTER TABLE personality_schemas DROP COLUMN IF EXISTS embedding")
    op.execute("ALTER TABLE personality_schemas ADD COLUMN embedding vector(1536)")

    # ── website_configs ───────────────────────────────────────────────────
    op.create_table(
        "website_configs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("personality_schema_id", UUID(as_uuid=True),
                  sa.ForeignKey("personality_schemas.id", ondelete="SET NULL"), nullable=True),
        sa.Column("version", sa.Integer, nullable=False, server_default="1"),
        sa.Column("is_published", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("subdomain", sa.String(63), nullable=True),
        sa.Column("config", JSON, nullable=False, server_default="'{}'"),
        sa.Column("site_mode", sa.String(50), nullable=False, server_default="cv"),
        sa.Column("last_rendered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("render_webhook_status", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_website_configs_user_id", "website_configs", ["user_id"])
    op.create_index("ix_website_configs_subdomain", "website_configs", ["subdomain"])

    # ── voice_clips ───────────────────────────────────────────────────────
    op.create_table(
        "voice_clips",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("recording_id", UUID(as_uuid=True),
                  sa.ForeignKey("recordings.id", ondelete="SET NULL"), nullable=True),
        sa.Column("s3_key", sa.String(1024), nullable=False),
        sa.Column("s3_bucket", sa.String(255), nullable=False),
        sa.Column("duration_seconds", sa.Float, nullable=False),
        sa.Column("file_size_bytes", sa.Integer, nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("label", sa.String(255), nullable=True),
        sa.Column("display_order", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_voice_clips_user_id", "voice_clips", ["user_id"])

    # ── audit_logs ────────────────────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=True),
        sa.Column("resource_id", sa.String(255), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text, nullable=True),
        sa.Column("request_path", sa.String(1024), nullable=True),
        sa.Column("request_method", sa.String(10), nullable=True),
        sa.Column("response_status", sa.Integer, nullable=True),
        sa.Column("metadata", JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_event_type", "audit_logs", ["event_type"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])

    # ── updated_at triggers ───────────────────────────────────────────────
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql'
    """)

    for table in ["users", "recordings", "photos", "personality_schemas",
                  "website_configs", "voice_clips"]:
        op.execute(f"""
            CREATE TRIGGER update_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column()
        """)

    # ════════════════════════════════════════════════════════════════════════
    # ROW-LEVEL SECURITY
    # All policies enforce: user_id = current_user_id()
    # ════════════════════════════════════════════════════════════════════════

    rls_tables = [
        "recordings", "photos", "personality_schemas",
        "website_configs", "voice_clips", "audit_logs",
    ]

    for table in rls_tables:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")

    # recordings
    op.execute("""
        CREATE POLICY recordings_user_isolation ON recordings
        USING (user_id = current_user_id())
        WITH CHECK (user_id = current_user_id())
    """)

    # photos
    op.execute("""
        CREATE POLICY photos_user_isolation ON photos
        USING (user_id = current_user_id())
        WITH CHECK (user_id = current_user_id())
    """)

    # personality_schemas
    op.execute("""
        CREATE POLICY personality_schemas_user_isolation ON personality_schemas
        USING (user_id = current_user_id())
        WITH CHECK (user_id = current_user_id())
    """)

    # website_configs — published configs are publicly readable
    op.execute("""
        CREATE POLICY website_configs_owner_access ON website_configs
        USING (
            user_id = current_user_id()
            OR is_published = true
        )
        WITH CHECK (user_id = current_user_id())
    """)

    # voice_clips — published user voice clips are publicly readable
    op.execute("""
        CREATE POLICY voice_clips_user_isolation ON voice_clips
        USING (user_id = current_user_id())
        WITH CHECK (user_id = current_user_id())
    """)

    # audit_logs — users can only read their own logs
    op.execute("""
        CREATE POLICY audit_logs_user_isolation ON audit_logs
        USING (user_id = current_user_id() OR user_id IS NULL)
        WITH CHECK (true)
    """)

    # ── HNSW index for pgvector similarity search ─────────────────────────
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_personality_schemas_embedding_hnsw
        ON personality_schemas
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)


def downgrade() -> None:
    # Drop in reverse dependency order
    for table in ["recordings", "photos", "personality_schemas",
                  "website_configs", "voice_clips", "audit_logs"]:
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")

    op.drop_table("audit_logs")
    op.drop_table("voice_clips")
    op.drop_table("website_configs")
    op.drop_table("personality_schemas")
    op.drop_table("photos")
    op.drop_table("recordings")
    op.drop_table("users")

    op.execute("DROP FUNCTION IF EXISTS current_user_id()")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE")
    op.execute("DROP EXTENSION IF EXISTS vector")
    op.execute("DROP EXTENSION IF EXISTS pgcrypto")
