-- Initial PostgreSQL setup script
-- Runs once when Docker container initializes a fresh database

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;

-- Create application roles (will be managed by Alembic migrations)
-- This script just ensures extensions are available at DB creation time.
