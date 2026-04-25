# Character-Websites (CW)

Lokale Startanleitung fuer das Projekt (Backend + Frontend + Omi + Integration).

## Voraussetzungen

- Python `3.10+` (empfohlen: `3.11`)
- Node.js `18+` (empfohlen: `20+`)
- npm
- Zugriff auf Supabase-Keys und weitere ENV-Werte

## 1) Environment konfigurieren

Im Projekt-Root:

```bash
cp .env.example .env.local
```

Dann `.env.local` mit echten Werten fuellen (mindestens):

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY` (nur Backend/Worker)
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `NEXT_PUBLIC_API_URL`
- `ANTHROPIC_API_KEY` (fuer Claude-Analyse)

## 2) Backend starten (FastAPI)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Checks:

- API: [http://localhost:8000](http://localhost:8000)
- Health: [http://localhost:8000/health](http://localhost:8000/health)
- Swagger (wenn `DEBUG=true`): [http://localhost:8000/docs](http://localhost:8000/docs)

## 3) Frontend starten (Next.js)

Neues Terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend auf: [http://localhost:3000](http://localhost:3000)

## 4) Optional: Celery Worker starten

Wenn du die asynchrone Analyse-Pipeline testen willst, in einem weiteren Terminal:

```bash
cd backend
source .venv/bin/activate
celery -A app.jobs.celery_app:celery_app worker --loglevel=info --concurrency=2 --queues=analysis,webhooks,default
```

## 5) Optional: Omi-Integration testen

```bash
pip install -r omi/requirements.txt
pytest omi/tests/ -v
```

Hinweis: Fuer echte Omi-Tests werden gueltige Omi OAuth/Device-Daten benoetigt.

## 6) Integrationstests

```bash
pytest integration/test_pipeline.py -q
```

Wichtig:

- `SUPABASE_SERVICE_ROLE_KEY` muss gesetzt sein, sonst schlagen die Integrationstests sofort fehl.
- Teile keine Service-Keys im Frontend.

## Projektstruktur (kurz)

- `backend/` - FastAPI API, Security, Upload/Retrieve-Routen, Jobs
- `frontend/` - Next.js App Router Frontend
- `omi/` - Omi Device Pairing, Sync, Acoustic/Privacy
- `integration/` - End-to-End/Integrations-Checks
- `supabase/` - Migrationen, Seed, Konfiguration
- `docs/` - Endnutzer- und Projektdokumentation

## User-Dokumentation (Omi)

- Omi Pairing Guide: `docs/OMI_PAIRING_USER_GUIDE.md`

## CI/CD & Tests

GitHub Actions laufen automatisch bei jedem Push und Pull Request gegen `main`.

Workflows (`.github/workflows/`):

- `ci.yml` — drei parallele Jobs:
  - **Backend**: pytest + Coverage (Min. 40 %), Redis-Service-Container
  - **Omi**: pytest + Coverage (Min. 30 %), inkl. Audio-Tooling
  - **Frontend**: ESLint, TypeScript-Check, Next.js Build
  - **CI passed**: Aggregat-Job als Required Check fuer Branch Protection
- `deploy-vercel.yml` — Optionales Auto-Deploy zu Vercel (nach gruener CI), gated ueber Repo-Variable `ENABLE_VERCEL_DEPLOY=true` und Secrets `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`

Lokale Entsprechungen:

```bash
# Backend
cd backend
pytest --cov=app --cov-report=term-missing

# Omi
cd omi
pytest --cov=. --cov-report=term-missing

# Frontend
cd frontend
npm run lint && npx tsc --noEmit && npm run build
```

Branch Protection (empfohlen, einmalig im Repo aktivieren):

1. GitHub -> Settings -> Branches -> Add rule fuer `main`
2. **Require status checks to pass**: `CI passed`
3. **Require pull request reviews before merging**
4. **Require linear history**

Dependabot ist aktiviert (`.github/dependabot.yml`) — woechentliche PRs fuer pip, npm und GitHub Actions.

## Typischer lokaler Start (Kurzfassung)

1. `.env.local` befuellen
2. Backend auf `:8000` starten
3. Frontend auf `:3000` starten
4. Optional Celery Worker starten
5. Health-Check + zentrale Flows testen
