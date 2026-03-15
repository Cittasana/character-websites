# V1 Launch Checklist

## Infrastructure — Done
- [x] Supabase project created (yeiizwkinffsjtfmvjio, Frankfurt)
- [x] 7 tables with RLS policies
- [x] pgvector extension enabled
- [x] 3 storage buckets configured
- [x] Seed data: demo user + personality schema + voice clips

## Backend
- [ ] ANTHROPIC_API_KEY set in production env
- [ ] Redis instance provisioned (Railway / Upstash / Redis Cloud)
- [ ] Backend deployed (Railway / Fly.io / VPS)
- [ ] Celery worker deployed alongside API
- [ ] POST /auth/register tested end-to-end
- [ ] POST /api/upload/voice tested with real audio file

## Frontend
- [ ] Vercel project created and linked to repo
- [ ] NEXT_PUBLIC_SUPABASE_URL + ANON_KEY set in Vercel env
- [ ] NEXT_PUBLIC_API_URL set to production backend URL
- [ ] Wildcard domain *.characterwebsites.com → Vercel
- [ ] demo.characterwebsites.com resolves and renders correctly

## Omi Integration
- [x] Omi App ID registered: 01KKSDZ90V6G699A82QY8PW5Z2
- [x] OMI_APP_ID + OMI_CLIENT_ID set (01KKSDZ90V6G699A82QY8PW5Z2) — client_secret optional for public app
- [ ] Device pairing tested with real Omi device

## Security
- [ ] SUPABASE_SERVICE_ROLE_KEY never exposed to frontend (verify)
- [ ] All storage buckets confirmed private (voice-recordings, user-photos)
- [ ] Rate limiting verified on upload routes

## Go-Live
- [ ] Founder's own account created (not demo UUID)
- [ ] Real personality data captured (7+ days of Omi recordings)
- [ ] Character website live at [username].characterwebsites.com
