-- Supabase Storage bucket definitions and access policies
-- Paths: {user_id}/{filename} — first path segment must match auth.uid() for JWT clients.
-- FastAPI uses the service role key; Storage RLS is bypassed for those requests.

-- 1. Voice recordings (private — app uses signed URLs where needed)
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'voice-recordings',
  'voice-recordings',
  false,
  52428800,  -- 50MB
  array['audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/x-wav', 'audio/mp4', 'audio/m4a', 'audio/x-m4a']
) on conflict (id) do nothing;

-- 2. Voice clips (private)
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'voice-clips',
  'voice-clips',
  false,
  20971520,  -- 20MB
  array['audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/x-wav', 'audio/mp4', 'audio/m4a', 'audio/x-m4a']
) on conflict (id) do nothing;

-- 3. User photos (private)
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'user-photos',
  'user-photos',
  false,
  10485760,  -- 10MB
  array['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
) on conflict (id) do nothing;

-- voice-recordings
create policy "voice_recordings_upload_own" on storage.objects
  for insert to authenticated
  with check (
    bucket_id = 'voice-recordings'
    and (storage.foldername(name))[1] = (select auth.uid()::text)
  );

create policy "voice_recordings_select_own" on storage.objects
  for select to authenticated
  using (
    bucket_id = 'voice-recordings'
    and (storage.foldername(name))[1] = (select auth.uid()::text)
  );

create policy "voice_recordings_delete_own" on storage.objects
  for delete to authenticated
  using (
    bucket_id = 'voice-recordings'
    and (storage.foldername(name))[1] = (select auth.uid()::text)
  );

-- user-photos
create policy "user_photos_upload_own" on storage.objects
  for insert to authenticated
  with check (
    bucket_id = 'user-photos'
    and (storage.foldername(name))[1] = (select auth.uid()::text)
  );

create policy "user_photos_select_own" on storage.objects
  for select to authenticated
  using (
    bucket_id = 'user-photos'
    and (storage.foldername(name))[1] = (select auth.uid()::text)
  );

create policy "user_photos_delete_own" on storage.objects
  for delete to authenticated
  using (
    bucket_id = 'user-photos'
    and (storage.foldername(name))[1] = (select auth.uid()::text)
  );

-- voice-clips (no public bucket read — use signed URLs from the API)
create policy "voice_clips_upload_own" on storage.objects
  for insert to authenticated
  with check (
    bucket_id = 'voice-clips'
    and (storage.foldername(name))[1] = (select auth.uid()::text)
  );

create policy "voice_clips_select_own" on storage.objects
  for select to authenticated
  using (
    bucket_id = 'voice-clips'
    and (storage.foldername(name))[1] = (select auth.uid()::text)
  );

create policy "voice_clips_delete_own" on storage.objects
  for delete to authenticated
  using (
    bucket_id = 'voice-clips'
    and (storage.foldername(name))[1] = (select auth.uid()::text)
  );
