# ⚠️ STACK UPDATE — READ BEFORE CONTINUING

**Date:** 2026-03-15
**Priority:** HIGH — adapt current work immediately

## Stack Change

The user confirmed:
- **Database / Auth / Storage → Supabase** (not raw PostgreSQL / custom JWT / custom S3)
- **Deployment → Vercel** (not Railway / Docker / Nginx)

## What This Means Per Team

### Team Backend
**STOP using:**
- Alembic migrations → use **Supabase CLI migrations** (`supabase/migrations/*.sql`)
- Raw SQLAlchemy/psycopg2 for DB access → use **`supabase-py`** client
- Custom JWT implementation → use **Supabase Auth** (`supabase.auth.*`)
- Custom S3 storage → use **Supabase Storage** (`supabase.storage.*`)
- Dockerfile + railway.toml → **delete or ignore** — deployment is Vercel / Supabase

**KEEP:**
- FastAPI routes structure (stays the same)
- Celery + Redis for async jobs (Celery connects to Supabase Postgres via DATABASE_URL)
- RLS policies (port them to Supabase SQL migrations)
- librosa acoustic analysis (unchanged)
- Claude API analysis (unchanged)

**Migration path:**
1. `app/database.py` → initialize `supabase-py` client using `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY`
2. `app/auth/` → use `supabase.auth.sign_up()`, `supabase.auth.sign_in_with_password()`, validate JWT via Supabase
3. `app/storage.py` → use `supabase.storage.from_("voice-recordings").upload(...)`
4. `migrations/` → convert to `supabase/migrations/YYYYMMDDHHMMSS_name.sql` raw SQL files
5. Remove `Dockerfile`, `railway.toml`, `nginx/`

### Team Frontend
**Minimal changes:**
- Add `@supabase/supabase-js` and `@supabase/ssr` for auth + data access
- Deployment: `vercel.json` or zero-config (Next.js on Vercel works out of the box)
- No Dockerfile needed
- For auth: use `createServerClient` from `@supabase/ssr` in middleware

**KEEP:** Everything else (Next.js App Router, personas, components, etc.)

### Team Omi
**Minor changes:**
- Use `supabase-py` for direct DB inserts instead of raw psycopg2
- Supabase Storage for file uploads (alternative to backend `/api/upload/voice` — or keep using the API endpoint, either is fine)
- No deployment config needed for this Python module

## Supabase Env Variables (use these names)
```
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...  # backend only, never expose to frontend
```

## Vercel Env Variables (frontend)
```
NEXT_PUBLIC_SUPABASE_URL=...
NEXT_PUBLIC_SUPABASE_ANON_KEY=...
NEXT_PUBLIC_API_URL=...  # backend FastAPI URL if separate
```
