# Character-Websites

## What This Is

Character-Websites is a premium SaaS platform (EUR 1,000 one-time) that captures a person's authentic character through Omi wearable voice recordings and photos, then uses Claude AI to generate a unique, dynamically evolving personal website. Each user gets a personal subdomain (e.g. cosmo.characterwebsites.com) where their personality drives every visual and structural decision.

## Core Value

**Authenticity over curation** — the website grows with who you actually are, not who you want to appear to be.

## Requirements

### Validated

(None yet — ship to validate)

### Active

**Backend API & Database:**
- [ ] FastAPI with two isolated route families: /api/upload/* and /api/retrieve/*
- [ ] PostgreSQL with Row-Level Security + pgvector for personality embeddings
- [ ] Celery + Redis job queue for async Claude analysis pipeline
- [ ] Claude personality analysis → structured JSON schema (7 dimensions + persona blend)
- [ ] JWT auth, file validation, malware scanning, rate limiting on upload routes
- [ ] Subdomain-to-user mapping via Nginx reverse proxy
- [ ] S3-compatible encrypted storage for voice and photo files
- [ ] Full audit logging on all ingest events

**Frontend Rendering Engine:**
- [ ] Next.js 14+ with App Router and wildcard subdomain middleware
- [ ] 4 core design personas: Minimalist-Refined, Maximalist-Bold, Organic-Warm, Structured-Professional
- [ ] Compositional persona blending via CSS custom properties from personality schema
- [ ] Dynamic layout engine (grid density, asymmetry, whitespace, flow direction)
- [ ] CV Mode: hero, personality insights, experience, interactive Q&A, calendar booking
- [ ] Dating Mode: avatar gallery, voice clip player, personality scores, values section
- [ ] Voice synthesis Q&A — employer types question, gets response in user's voice
- [ ] Framer Motion personality-driven micro-interactions
- [ ] ISR — website re-renders within 60s of new personality schema

**Omi Integration:**
- [ ] Omi SDK device pairing flow (Bluetooth + OAuth 2.0)
- [ ] Automatic background voice data sync to /api/upload/voice
- [ ] Acoustic metadata extraction (pitch, rhythm, emotional cadence, pause patterns)
- [ ] Transcript handling (Omi-generated + Whisper fallback)
- [ ] Deduplication logic for recordings
- [ ] User privacy controls (delete recording, reset profile, disable sync)
- [ ] Offline queue for recordings captured without internet

### Out of Scope

- **Mobile App (iOS/Android)** — deferred; Omi sync will be handled via backend directly for now
- **Legacy Mode (digital memorial chatbot)** — V2 feature explicitly
- **Payment/billing system** — V1 launch handles manually or via external link
- **Multi-device Omi support** — V1 is single device per user
- **Custom domain (non-subdomain)** — V2; V1 uses characterwebsites.com subdomains only

## Context

Built from 5 comprehensive PRDs (March 2026):
- `files/01-Master-Summary.docx` — vision, architecture, GTM
- `files/03-PRD-Backend-API-Database.docx` — API design, DB schema, security
- `files/04-PRD-Frontend-Rendering-Engine.docx` — design system, rendering pipeline
- `files/05-PRD-Omi-Integration.docx` — device pairing, audio pipeline, privacy

Three parallel build tracks, each with dedicated agent team:
1. **Backend** — Python/FastAPI, PostgreSQL, Celery, Redis, Claude API
2. **Frontend** — Next.js 14+, Tailwind/CSS-in-JS, Framer Motion
3. **Omi** — Omi SDK, librosa acoustic analysis, data pipeline

4-week target to V1 launch. Founder's own character website = live proof of concept.

## Constraints

- **Tech Stack**: Python 3.11+ / FastAPI (backend), Next.js 14+ (frontend), PostgreSQL 15+ with pgvector — locked per PRD
- **AI Engine**: Claude API `claude-sonnet-4-20250514` for personality analysis
- **Deployment**: Docker + Nginx on Railway
- **Timeline**: 4 weeks to V1 (each track has weekly milestones)
- **Privacy**: Voice data never exposed to public APIs; raw audio auto-deletable after analysis
- **Security**: RLS at DB level — application-layer breach cannot access other users' data

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| One-time pricing EUR 1,000 | Positions as investment, not subscription; users own it | — Pending |
| PostgreSQL RLS over app-layer isolation | Defense in depth — DB enforces isolation even if app is breached | — Pending |
| Two isolated route families (upload vs retrieve) | Separate auth stacks, separate DB users, separate security policies | — Pending |
| Compositional persona blending (4 personas, weighted) | Each user gets truly unique visual identity, not template selection | — Pending |
| ISR for website rendering | Performance at scale, instant invalidation on schema update | — Pending |
| Celery + Redis for analysis queue | Decouples upload latency from Claude analysis time; retries built-in | — Pending |
| Skip mobile app for V1 backend/frontend/Omi build | Focus velocity on core platform; mobile deferred | — Pending |

---
*Last updated: 2026-03-15 after initialization from PRDs*
