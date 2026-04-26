#!/usr/bin/env bash
# Celery-Worker auf Railway per CLI anlegen (nach: railway login)
# Voraussetzung: Repo-Root auf Railway = backend/ dieses Repos; GitHub-App hat Zugriff auf die Org.
#
# Optional überschreiben:
#   RAILWAY_PROJECT=Character-Webistes RAILWAY_ENV=production \
#   RAILWAY_LINK_SERVICE=Character-Webistes CELERY_SERVICE_NAME=celery-worker \
#   GITHUB_REPO=Cittasana/character-websites ./scripts/setup-railway-celery-worker.sh

set -euo pipefail
cd "$(dirname "$0")/.."

PROJECT="${RAILWAY_PROJECT:-Character-Webistes}"
ENV="${RAILWAY_ENV:-production}"
LINK_SVC="${RAILWAY_LINK_SERVICE:-Character-Webistes}"
SVC_NAME="${CELERY_SERVICE_NAME:-celery-worker}"
REPO="${GITHUB_REPO:-Cittasana/character-websites}"

echo "==> Link: Projekt=${PROJECT} Env=${ENV} Service=${LINK_SVC}"
railway link -p "$PROJECT" -e "$ENV" -s "$LINK_SVC"

echo "==> Neuer Service: ${SVC_NAME} <- ${REPO}"
railway add --service "$SVC_NAME" --repo "$REPO" --variables "RAILWAY_CLI_PLACEHOLDER=1"

echo
echo "==> Nächste Schritte im Railway-Dashboard (CLI setzt das oft nicht):"
echo "    1) Service ${SVC_NAME} → Settings → Source → Root Directory: /backend"
echo "    2) Config as code (Repo-Wurzel, NICHT /railway…): /backend/railway.celery.toml"
echo "    3) Variables: wie beim API-Service (inkl. REDIS_URL / CELERY_* / Supabase / ANTHROPIC)"
echo "    4) Deploy"
echo
echo "Falls railway add mit 'Unauthorized' endet: login prüfen, unset RAILWAY_TOKEN, GitHub-Org-Zugriff für Railway-App, oder Worker nur im UI anlegen."
