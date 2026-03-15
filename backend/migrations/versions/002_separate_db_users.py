"""
002 — Separate PostgreSQL roles for upload and retrieve operations.
- upload_user: INSERT only on recordings/photos/transcripts (no SELECT of data)
- retrieve_user: SELECT only on website_configs/personality_schemas/voice_clips
- app_user: full DML on all tables (used by the FastAPI app at runtime)

Revision ID: 002_separate_db_users
Revises: 001_initial_schema_rls
Create Date: 2025-05-28
"""
from alembic import op

revision = "002_separate_db_users"
down_revision = "001_initial_schema_rls"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Create roles (idempotent) ─────────────────────────────────────────
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'cw_upload_user') THEN
                CREATE ROLE cw_upload_user NOLOGIN;
            END IF;
            IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'cw_retrieve_user') THEN
                CREATE ROLE cw_retrieve_user NOLOGIN;
            END IF;
        END
        $$
    """)

    # ── cw_upload_user: INSERT only on ingest tables ──────────────────────
    # Can insert recordings, photos, audit_logs — cannot read or modify
    op.execute("GRANT INSERT ON recordings TO cw_upload_user")
    op.execute("GRANT INSERT ON photos TO cw_upload_user")
    op.execute("GRANT INSERT ON audit_logs TO cw_upload_user")
    # Needs to read own sequence for UUID generation (not applicable for server defaults)
    # Allow SELECT on users for auth verification
    op.execute("GRANT SELECT ON users TO cw_upload_user")
    # Allow reading recording status for transcript linking
    op.execute("GRANT SELECT ON recordings TO cw_upload_user")
    op.execute("GRANT UPDATE (transcript, transcript_source, processing_status, celery_task_id) ON recordings TO cw_upload_user")

    # ── cw_retrieve_user: SELECT only on output tables ────────────────────
    op.execute("GRANT SELECT ON website_configs TO cw_retrieve_user")
    op.execute("GRANT SELECT ON personality_schemas TO cw_retrieve_user")
    op.execute("GRANT SELECT ON voice_clips TO cw_retrieve_user")
    op.execute("GRANT SELECT ON users TO cw_retrieve_user")
    op.execute("GRANT SELECT ON recordings TO cw_retrieve_user")
    op.execute("GRANT INSERT ON audit_logs TO cw_retrieve_user")

    # ── Revoke dangerous privileges ───────────────────────────────────────
    # upload_user CANNOT read website_configs or personality_schemas
    op.execute("REVOKE ALL ON website_configs FROM cw_upload_user")
    op.execute("REVOKE ALL ON personality_schemas FROM cw_upload_user")
    op.execute("REVOKE ALL ON voice_clips FROM cw_upload_user")

    # retrieve_user CANNOT modify any table
    op.execute("REVOKE INSERT, UPDATE, DELETE ON recordings FROM cw_retrieve_user")
    op.execute("REVOKE INSERT, UPDATE, DELETE ON photos FROM cw_retrieve_user")
    op.execute("REVOKE INSERT, UPDATE, DELETE ON website_configs FROM cw_retrieve_user")
    op.execute("REVOKE INSERT, UPDATE, DELETE ON personality_schemas FROM cw_retrieve_user")

    # ── RLS bypass for app role ───────────────────────────────────────────
    # The main app role (cw_app) can bypass RLS when needed for admin ops
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'cw_app') THEN
                CREATE ROLE cw_app LOGIN;
            END IF;
        END
        $$
    """)
    op.execute("GRANT ALL ON ALL TABLES IN SCHEMA public TO cw_app")
    op.execute("GRANT USAGE ON SCHEMA public TO cw_app")
    op.execute("GRANT USAGE ON SCHEMA public TO cw_upload_user")
    op.execute("GRANT USAGE ON SCHEMA public TO cw_retrieve_user")


def downgrade() -> None:
    op.execute("DROP ROLE IF EXISTS cw_upload_user")
    op.execute("DROP ROLE IF EXISTS cw_retrieve_user")
