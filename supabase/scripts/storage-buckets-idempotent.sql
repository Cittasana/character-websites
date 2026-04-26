-- ═══════════════════════════════════════════════════════════════════════════
-- Supabase Storage: Buckets + RLS (idempotent)
-- Ausführung: Dashboard → SQL → New query → Run
-- Pfade im Backend: {user_id}/{filename}  → erster Ordner = auth.uid()
-- Service Role (FastAPI) umgeht RLS — Upload/Download/Signed URLs funktionieren.
-- ═══════════════════════════════════════════════════════════════════════════

-- ── Buckets (privat, Größen/MIME wie im Backend) ────────────────────────────
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values
  (
    'voice-recordings',
    'voice-recordings',
    false,
    52428800, -- 50 MB
    array[
      'audio/mpeg',
      'audio/mp3',
      'audio/wav',
      'audio/x-wav',
      'audio/mp4',
      'audio/m4a',
      'audio/x-m4a'
    ]
  ),
  (
    'voice-clips',
    'voice-clips',
    false,
    20971520, -- 20 MB
    array[
      'audio/mpeg',
      'audio/mp3',
      'audio/wav',
      'audio/x-wav',
      'audio/mp4',
      'audio/m4a',
      'audio/x-m4a'
    ]
  ),
  (
    'user-photos',
    'user-photos',
    false,
    10485760, -- 10 MB
    array['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
  )
on conflict (id) do update set
  public = excluded.public,
  file_size_limit = excluded.file_size_limit,
  allowed_mime_types = excluded.allowed_mime_types;

-- ── Alte Policies entfernen (Migration oder frühere Versuche) ─────────────
drop policy if exists "voice_recordings_upload_own" on storage.objects;
drop policy if exists "voice_recordings_select_own" on storage.objects;
drop policy if exists "voice_recordings_delete_own" on storage.objects;
drop policy if exists "voice_recordings_service_all" on storage.objects;

drop policy if exists "user_photos_upload_own" on storage.objects;
drop policy if exists "user_photos_select_own" on storage.objects;
drop policy if exists "user_photos_delete_own" on storage.objects;
drop policy if exists "user_photos_service_all" on storage.objects;

drop policy if exists "voice_clips_service_all" on storage.objects;
drop policy if exists "voice_clips_select_public" on storage.objects;
drop policy if exists "voice_clips_upload_own" on storage.objects;
drop policy if exists "voice_clips_select_own" on storage.objects;
drop policy if exists "voice_clips_delete_own" on storage.objects;

-- ── voice-recordings: nur eigener Ordner (JWT), Backend = Service Role ───
create policy "voice_recordings_upload_own"
  on storage.objects for insert to authenticated
  with check (
    bucket_id = 'voice-recordings'
    and (storage.foldername(name))[1] = (select auth.uid()::text)
  );

create policy "voice_recordings_select_own"
  on storage.objects for select to authenticated
  using (
    bucket_id = 'voice-recordings'
    and (storage.foldername(name))[1] = (select auth.uid()::text)
  );

create policy "voice_recordings_delete_own"
  on storage.objects for delete to authenticated
  using (
    bucket_id = 'voice-recordings'
    and (storage.foldername(name))[1] = (select auth.uid()::text)
  );

-- ── user-photos ───────────────────────────────────────────────────────────
create policy "user_photos_upload_own"
  on storage.objects for insert to authenticated
  with check (
    bucket_id = 'user-photos'
    and (storage.foldername(name))[1] = (select auth.uid()::text)
  );

create policy "user_photos_select_own"
  on storage.objects for select to authenticated
  using (
    bucket_id = 'user-photos'
    and (storage.foldername(name))[1] = (select auth.uid()::text)
  );

create policy "user_photos_delete_own"
  on storage.objects for delete to authenticated
  using (
    bucket_id = 'user-photos'
    and (storage.foldername(name))[1] = (select auth.uid()::text)
  );

-- ── voice-clips: kein öffentliches Listing; Zugriff über Signed URLs (API)
create policy "voice_clips_upload_own"
  on storage.objects for insert to authenticated
  with check (
    bucket_id = 'voice-clips'
    and (storage.foldername(name))[1] = (select auth.uid()::text)
  );

create policy "voice_clips_select_own"
  on storage.objects for select to authenticated
  using (
    bucket_id = 'voice-clips'
    and (storage.foldername(name))[1] = (select auth.uid()::text)
  );

create policy "voice_clips_delete_own"
  on storage.objects for delete to authenticated
  using (
    bucket_id = 'voice-clips'
    and (storage.foldername(name))[1] = (select auth.uid()::text)
  );
