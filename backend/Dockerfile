# ══════════════════════════════════════════════════════════════════════════════
# Character-Websites Backend — Production Dockerfile
# Multi-stage build: deps + app
# No libpq/asyncpg — database is Supabase (remote, HTTP-based via supabase-py)
# ══════════════════════════════════════════════════════════════════════════════

# ── Stage 1: Build dependencies ────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# System deps needed for librosa, python-magic, Pillow, soundfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libmagic1 \
    libmagic-dev \
    libsndfile1 \
    libsndfile1-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps to a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── Stage 2: Runtime image ────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Runtime system deps only (no libpq needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    libsndfile1 \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && addgroup --system appgroup \
    && adduser --system --ingroup appgroup --no-create-home appuser

# Copy venv from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY app/ ./app/

# Set non-root user
USER appuser

# ── Environment defaults (override at runtime) ────────────────────────────────
# PORT wird von Railway gesetzt; lokal z. B. 8000
ENV APP_ENV=production \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PORT=8000

SHELL ["/bin/sh", "-c"]

# Expose (Hinweis für lokal; Railway setzt die öffentliche Port-Weiterleitung über $PORT)
EXPOSE 8000

# Health check (läuft mit Shell, damit $PORT expandiert)
HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -fsS "http://127.0.0.1:${PORT}/health" >/dev/null || exit 1

# Uvicorn: $PORT für Railway / PaaS; weniger Worker = weniger RAM auf kleinen Plänen
CMD uvicorn app.main:app \
     --host 0.0.0.0 \
     --port "${PORT}" \
     --workers 2 \
     --log-level info \
     --access-log \
     --proxy-headers \
     --forwarded-allow-ips '*'
