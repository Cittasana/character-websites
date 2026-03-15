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
ENV APP_ENV=production \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# ── Default: run FastAPI with Uvicorn (multi-worker) ─────────────────────────
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--log-level", "info", \
     "--access-log", \
     "--proxy-headers", \
     "--forwarded-allow-ips", "*"]
