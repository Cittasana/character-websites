<!-- Status updated 2026-03-15: Phases 1-13 COMPLETE. Phase 14 = Supabase migration, Phase 15 = Integration -->

# Roadmap: Character-Websites

## Overview

Three parallel agent teams build Character-Websites simultaneously: the **Backend** team builds the FastAPI + PostgreSQL + Celery intelligence pipeline (Phases 1-5), the **Frontend** team builds the Next.js rendering engine and design system (Phases 6-10), and the **Omi** team builds the wearable integration and audio pipeline (Phases 11-13). All three tracks start at the same time. Phase 14 brings them together for end-to-end integration testing before V1 launch.

## Domain Expertise

None — standard web/API/audio patterns throughout.

## Agent Teams

Three teams work in parallel:
- **Team Backend**: Phases 1 → 2 → 3 → 4 → 5
- **Team Frontend**: Phases 6 → 7 → 8 → 9 → 10
- **Team Omi**: Phases 11 → 12 → 13

All teams converge at **Phase 14: Integration**.

## Phases

**Team Backend (sequential within team, parallel with other teams):**
- [ ] **Phase 1: Backend Foundation** - PostgreSQL schema, RLS policies, user auth, JWT
- [ ] **Phase 2: Upload Pipeline** - Upload routes, file validation, S3 storage, rate limiting, audit logging
- [ ] **Phase 3: Claude Analysis Pipeline** - Celery+Redis job queue, personality schema generation, acoustic analysis
- [ ] **Phase 4: Retrieve Routes & Subdomain** - Retrieve endpoints, Nginx subdomain routing, CDN caching
- [ ] **Phase 5: Backend Security & Hardening** - Security audit, load testing, deployment to Railway

**Team Frontend (sequential within team, parallel with other teams):**
- [ ] **Phase 6: Frontend Foundation** - Next.js 14+ setup, wildcard subdomain middleware, design token architecture
- [ ] **Phase 7: Design System & Persona Engine** - 4 personas, compositional blending, CSS token injection, Framer Motion base
- [ ] **Phase 8: CV Mode** - Hero, personality insights, experience timeline, employer Q&A widget, calendar booking
- [ ] **Phase 9: Dating Mode & Voice Player** - Avatar display, voice clips gallery, personality scores, Web Audio waveform
- [ ] **Phase 10: Voice Q&A & Performance** - Real-time voice synthesis Q&A, ISR setup, Lighthouse optimization

**Team Omi (sequential within team, parallel with other teams):**
- [ ] **Phase 11: Omi SDK & Device Pairing** - Omi SDK setup, Bluetooth pairing flow, OAuth 2.0 device auth
- [ ] **Phase 12: Audio Sync Pipeline** - Background sync, deduplication, offline queue, transcript handling
- [ ] **Phase 13: Acoustic Analysis & Privacy** - librosa feature extraction, privacy controls, sync status UI

**Convergence:**
- [ ] **Phase 14: Integration & E2E** - Full pipeline test, cross-team integration, Railway deployment, V1 launch prep

---

## Phase Details

### Phase 1: Backend Foundation
**Goal**: Database schema with RLS, user authentication, JWT token system
**Team**: Backend
**Depends on**: Nothing (parallel start)
**Research**: Likely (PostgreSQL RLS + pgvector setup, JWT patterns for FastAPI)
**Research topics**: FastAPI JWT best practices, PostgreSQL RLS policy syntax, pgvector setup, Railway PostgreSQL config
**Plans**: 5 plans

Plans:
- [ ] 01-01: PostgreSQL schema — all 7 tables (users, recordings, photos, personality_schemas, website_configs, voice_clips, audit_logs)
- [ ] 01-02: Row-Level Security policies on all user data tables
- [ ] 01-03: pgvector extension setup + embedding column in personality_schemas
- [ ] 01-04: User authentication — JWT issue/validate/refresh
- [ ] 01-05: FastAPI app skeleton — project structure, Uvicorn config, middleware setup

### Phase 2: Upload Pipeline
**Goal**: Secure upload routes with file validation, S3 storage, rate limiting, and audit logging
**Team**: Backend
**Depends on**: Phase 1
**Research**: Likely (S3-compatible storage on Railway, malware scanning options, FastAPI file upload patterns)
**Research topics**: Railway S3-compatible object storage options, file malware scanning (clamd, VirusTotal), FastAPI multipart upload
**Plans**: 4 plans

Plans:
- [ ] 02-01: POST /api/upload/voice — multipart audio upload, JWT auth, file validation, size limits
- [ ] 02-02: POST /api/upload/photos — photo upload, validation, S3 storage
- [ ] 02-03: POST /api/upload/transcript — manual transcript submission
- [ ] 02-04: Rate limiting (100 req/hr/user), audit logging middleware, Nginx rate limiting config

### Phase 3: Claude Analysis Pipeline
**Goal**: Async Celery job queue processes uploads through Claude, outputs structured personality schema JSON
**Team**: Backend
**Depends on**: Phase 2
**Research**: Likely (Claude API structured output patterns, Celery + Redis setup, librosa acoustic feature extraction)
**Research topics**: Claude API JSON schema output, Celery workers on Railway, Redis on Railway, librosa pitch/rhythm extraction
**Plans**: 5 plans

Plans:
- [ ] 03-01: Celery + Redis setup — workers, broker config, job serialization
- [ ] 03-02: Upload → job queue trigger — new upload fires async Celery task
- [ ] 03-03: Acoustic metadata extraction — librosa pitch, rhythm, cadence, pause patterns
- [ ] 03-04: Claude personality analysis — transcript + acoustic data → 7-dimension JSON schema + persona blend weights
- [ ] 03-05: Schema storage + website regeneration trigger — versioned personality_schemas, webhook/ISR invalidation

### Phase 4: Retrieve Routes & Subdomain Routing
**Goal**: Public-facing retrieve API endpoints, Nginx wildcard subdomain routing, response caching
**Team**: Backend
**Depends on**: Phase 3
**Research**: Likely (Nginx wildcard subdomain config on Railway, CDN caching patterns, Railway custom domains)
**Research topics**: Railway custom domain + wildcard DNS, Nginx subdomain routing to Next.js, Redis caching for API responses
**Plans**: 4 plans

Plans:
- [ ] 04-01: GET /api/retrieve/website/:userId and GET /api/retrieve/personality/:userId
- [ ] 04-02: GET /api/retrieve/voiceclips/:userId — signed S3 URLs, POST /api/retrieve/qa
- [ ] 04-03: Nginx config — wildcard subdomain routing, SSL termination, rate limiting
- [ ] 04-04: Redis API response caching, ISR revalidation webhook endpoint

### Phase 5: Backend Security & Hardening
**Goal**: Security audit, separate DB users per route family, load testing, Railway production deployment
**Team**: Backend
**Depends on**: Phase 4
**Research**: Unlikely (internal hardening patterns)
**Plans**: 4 plans

Plans:
- [ ] 05-01: Separate PostgreSQL users for upload vs retrieve routes with scoped permissions
- [ ] 05-02: Encryption at rest validation, TLS enforcement, environment secrets audit
- [ ] 05-03: Load testing — upload pipeline, retrieve routes, Claude job queue throughput
- [ ] 05-04: Docker containerization + Railway deployment — production config, health checks

---

### Phase 6: Frontend Foundation
**Goal**: Next.js 14+ project with App Router, wildcard subdomain middleware, design token architecture
**Team**: Frontend
**Depends on**: Nothing (parallel start)
**Research**: Likely (Next.js 14 App Router subdomain middleware, CSS custom properties injection patterns, ISR config)
**Research topics**: Next.js middleware subdomain routing, CSS-in-JS vs Tailwind with dynamic tokens, Next.js ISR on-demand revalidation
**Plans**: 4 plans

Plans:
- [ ] 06-01: Next.js 14+ scaffold — App Router, TypeScript, project structure
- [ ] 06-02: Wildcard subdomain middleware — intercepts subdomain, fetches user personality schema
- [ ] 06-03: Design token architecture — CSS custom properties system for dynamic persona injection
- [ ] 06-04: API client layer — typed wrappers for /api/retrieve/* endpoints

### Phase 7: Design System & Persona Engine
**Goal**: 4 core personas with compositional blending, Framer Motion base animations, dynamic layout engine
**Team**: Frontend
**Depends on**: Phase 6
**Research**: Unlikely (design system is internal, well-specified in PRD)
**Plans**: 5 plans

Plans:
- [ ] 07-01: Minimalist-Refined persona — tokens (Playfair Display, monochromatic, generous whitespace)
- [ ] 07-02: Maximalist-Bold persona — tokens (Bebas Neue, vibrant multi-color, dense grid, diagonal flows)
- [ ] 07-03: Organic-Warm persona — tokens (Nunito, earth tones, curved sections, rounded components)
- [ ] 07-04: Structured-Professional persona — tokens (DM Sans, navy/grey, strict grid, card-based)
- [ ] 07-05: Compositional blending engine — weighted interpolation of tokens + dynamic layout engine (density, asymmetry, whitespace, flow)

### Phase 8: CV Mode
**Goal**: Full CV mode with hero, personality insights, experience timeline, employer Q&A, calendar booking
**Team**: Frontend
**Depends on**: Phase 7
**Research**: Unlikely (internal UI following established patterns + design system)
**Plans**: 4 plans

Plans:
- [ ] 08-01: CV Hero — name, headline, personality-driven positioning statement
- [ ] 08-02: Personality Insights section — Claude-generated character summary, dimension visualization
- [ ] 08-03: Experience & Achievements — timeline or card layout driven by layout directives
- [ ] 08-04: Schedule a Call widget — calendar booking integration (Calendly embed or similar)

### Phase 9: Dating Mode & Voice Player
**Goal**: Dating mode with avatar display, voice clips gallery, personality scores, Web Audio waveform player
**Team**: Frontend
**Depends on**: Phase 7
**Research**: Likely (Web Audio API waveform visualization, signed URL audio streaming)
**Research topics**: Web Audio API waveform visualization patterns, Next.js audio streaming with signed S3 URLs
**Plans**: 4 plans

Plans:
- [ ] 09-01: Dating Hero — avatar from photos, name, personality tagline
- [ ] 09-02: Voice Clips Gallery — audio player with Web Audio waveform visualization
- [ ] 09-03: Personality Scores — visual cards (warmth, humor, ambition, adventure)
- [ ] 09-04: Values section + Photo Reels — animated transitions, visual storytelling

### Phase 10: Voice Q&A & Performance
**Goal**: Real-time voice synthesis Q&A for CV mode, ISR configuration, Lighthouse score ≥85
**Team**: Frontend
**Depends on**: Phase 8 (CV mode complete)
**Research**: Likely (text-to-speech voice cloning options, Web Audio playback of synthesized speech)
**Research topics**: Browser TTS with voice samples, /api/retrieve/qa streaming response, Next.js ISR on-demand revalidation
**Plans**: 4 plans

Plans:
- [ ] 10-01: Voice Q&A widget — text input, /api/retrieve/qa call, synthesized audio response
- [ ] 10-02: Audio playback — waveform visualization for Q&A response, streaming if possible
- [ ] 10-03: ISR setup — on-demand revalidation on personality schema update, cache strategy
- [ ] 10-04: Performance polish — Lighthouse audit, image optimization, bundle analysis

---

### Phase 11: Omi SDK & Device Pairing
**Goal**: Omi SDK integration, Bluetooth pairing flow, OAuth 2.0 device auth, device ID linked to user
**Team**: Omi
**Depends on**: Nothing (parallel start, integrates with Backend Phase 1 user auth)
**Research**: Likely (Omi SDK documentation, Omi OAuth 2.0 flow, Omi API current state)
**Research topics**: Omi open-source SDK docs, Omi OAuth 2.0 device authorization flow, Omi API endpoints for recording retrieval
**Plans**: 4 plans

Plans:
- [ ] 11-01: Omi SDK setup — Python library install, SDK auth, device discovery
- [ ] 11-02: Device pairing flow — Bluetooth pairing, Omi OAuth 2.0, device ID → user account link
- [ ] 11-03: Re-pairing flow — device replacement, reset handling
- [ ] 11-04: Pairing status + confirmation — clear success/error states, device management UI data

### Phase 12: Audio Sync Pipeline
**Goal**: Automatic background voice sync, deduplication, offline queue, transcript handling with Whisper fallback
**Team**: Omi
**Depends on**: Phase 11
**Research**: Likely (Omi SDK polling vs webhook for new recordings, Whisper API for transcription fallback)
**Research topics**: Omi SDK new recording detection mechanism, OpenAI Whisper API / local Whisper for transcription, multipart upload to /api/upload/voice
**Plans**: 4 plans

Plans:
- [ ] 12-01: New recording detection — Omi SDK polling or webhook, download to encrypted local buffer
- [ ] 12-02: Upload to /api/upload/voice — multipart upload with JWT auth, sync status tracking
- [ ] 12-03: Deduplication logic — hash-based prevention of double-uploads
- [ ] 12-04: Offline queue + Whisper fallback — recordings queued without internet, transcription fallback if no Omi transcript

### Phase 13: Acoustic Analysis & Privacy Controls
**Goal**: librosa acoustic metadata extraction, user privacy controls (delete/reset/disable), sync status UI data
**Team**: Omi
**Depends on**: Phase 12
**Research**: Unlikely (librosa patterns established, privacy controls are CRUD)
**Plans**: 4 plans

Plans:
- [ ] 13-01: librosa integration — pitch range, speech rhythm, emotional cadence, pause patterns extraction
- [ ] 13-02: Acoustic metadata → Celery job — extracted features sent alongside transcript for Claude analysis
- [ ] 13-03: Privacy controls API — delete individual recording, delete all data + profile reset, disable sync
- [ ] 13-04: Sync status endpoints — last sync timestamp, recording count, sync health for app dashboard

---

### Phase 14: Integration & E2E
**Goal**: Full pipeline end-to-end test (Omi → Backend → Claude → Frontend), cross-team fixes, V1 launch readiness
**Team**: All teams converge
**Depends on**: Phases 5, 10, 13 (all tracks complete)
**Research**: Unlikely (integration of already-built systems)
**Plans**: 4 plans

Plans:
- [ ] 14-01: Full pipeline test — Omi upload → Claude analysis → personality schema → frontend re-render
- [ ] 14-02: Cross-team integration fixes — API contract validation, auth token flow, subdomain routing
- [ ] 14-03: Security end-to-end audit — RLS cross-user test, signed URL validation, rate limit verification
- [ ] 14-04: V1 launch checklist — DNS configuration, Railway production deploy, founder's character website live

---

## Progress

**Execution Order:**
- Start simultaneously: Phases 1, 6, 11 (three parallel teams)
- Each team continues sequentially within their track
- All converge at Phase 14

| Phase | Team | Plans Complete | Status | Completed |
|-------|------|----------------|--------|-----------|
| 1. Backend Foundation | Backend | 0/5 | Not started | - |
| 2. Upload Pipeline | Backend | 0/4 | Not started | - |
| 3. Claude Analysis Pipeline | Backend | 0/5 | Not started | - |
| 4. Retrieve Routes & Subdomain | Backend | 0/4 | Not started | - |
| 5. Backend Security & Hardening | Backend | 0/4 | Not started | - |
| 6. Frontend Foundation | Frontend | 0/4 | Not started | - |
| 7. Design System & Persona Engine | Frontend | 0/5 | Not started | - |
| 8. CV Mode | Frontend | 0/4 | Not started | - |
| 9. Dating Mode & Voice Player | Frontend | 0/4 | Not started | - |
| 10. Voice Q&A & Performance | Frontend | 0/4 | Not started | - |
| 11. Omi SDK & Device Pairing | Omi | 0/4 | Not started | - |
| 12. Audio Sync Pipeline | Omi | 0/4 | Not started | - |
| 13. Acoustic Analysis & Privacy | Omi | 0/4 | Not started | - |
| 14. Integration & E2E | All | 0/4 | Not started | - |
