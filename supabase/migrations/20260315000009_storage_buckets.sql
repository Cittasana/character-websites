-- Supabase Storage bucket definitions and access policies

-- 1. Voice recordings (private — signed URLs only)
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'voice-recordings',
  'voice-recordings',
  false,
  52428800,  -- 50MB
  array['audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/x-wav', 'audio/mp4', 'audio/m4a', 'audio/x-m4a']
) on conflict (id) do nothing;

-- 2. Voice clips (private — signed URLs, publicly accessible if clip.is_public)
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'voice-clips',
  'voice-clips',
  false,
  20971520,  -- 20MB
  array['audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/x-wav', 'audio/mp4', 'audio/m4a']
) on conflict (id) do nothing;

-- 3. User photos (private — signed URLs)
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
  'user-photos',
  'user-photos',
  false,
  10485760,  -- 10MB
  array['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
) on conflict (id) do nothing;

-- Storage RLS policies

-- voice-recordings: users can upload/read only their own folder
create policy "voice_recordings_upload_own" on storage.objects
  for insert with check (
    bucket_id = 'voice-recordings'
    and auth.uid()::text = (storage.foldername(name))[1]
  );

create policy "voice_recordings_select_own" on storage.objects
  for select using (
    bucket_id = 'voice-recordings'
    and auth.uid()::text = (storage.foldername(name))[1]
  );

create policy "voice_recordings_delete_own" on storage.objects
  for delete using (
    bucket_id = 'voice-recordings'
    and auth.uid()::text = (storage.foldername(name))[1]
  );

create policy "voice_recordings_service_all" on storage.objects
  for all using (
    bucket_id = 'voice-recordings'
    and auth.role() = 'service_role'
  );

-- user-photos: same pattern
create policy "user_photos_upload_own" on storage.objects
  for insert with check (
    bucket_id = 'user-photos'
    and auth.uid()::text = (storage.foldername(name))[1]
  );

create policy "user_photos_select_own" on storage.objects
  for select using (
    bucket_id = 'user-photos'
    and auth.uid()::text = (storage.foldername(name))[1]
  );

create policy "user_photos_delete_own" on storage.objects
  for delete using (
    bucket_id = 'user-photos'
    and auth.uid()::text = (storage.foldername(name))[1]
  );

create policy "user_photos_service_all" on storage.objects
  for all using (
    bucket_id = 'user-photos'
    and auth.role() = 'service_role'
  );

-- voice-clips: service writes, public reads (clips served on dating profile)
create policy "voice_clips_service_all" on storage.objects
  for all using (
    bucket_id = 'voice-clips'
    and auth.role() = 'service_role'
  );

create policy "voice_clips_select_public" on storage.objects
  for select using (bucket_id = 'voice-clips');
