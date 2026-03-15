-- Voice recordings uploaded from Omi device
create table public.recordings (
  id              uuid primary key default gen_random_uuid(),
  user_id         uuid not null references public.users(id) on delete cascade,
  storage_path    text not null,               -- Supabase Storage path: voice-recordings/{user_id}/{filename}
  original_filename text,
  duration_seconds float,
  file_size_bytes bigint,
  mime_type       text not null default 'audio/mpeg',
  sha256_hash     text not null,               -- deduplication key
  omi_recording_id text,                       -- Omi cloud ID for deduplication
  language        text default 'de',
  processing_status text not null default 'pending'
    check (processing_status in ('pending', 'processing', 'complete', 'failed')),
  acoustic_metadata jsonb,                     -- librosa extraction output
  exclude_from_analysis boolean not null default false,
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);

create index recordings_user_id_idx on public.recordings (user_id);
create index recordings_sha256_idx on public.recordings (sha256_hash);
create index recordings_omi_id_idx on public.recordings (omi_recording_id) where omi_recording_id is not null;
create index recordings_status_idx on public.recordings (processing_status) where processing_status = 'pending';

alter table public.recordings enable row level security;

create policy "recordings_select_own" on public.recordings
  for select using (auth.uid() = user_id);

create policy "recordings_insert_own" on public.recordings
  for insert with check (auth.uid() = user_id);

create policy "recordings_update_own" on public.recordings
  for update using (auth.uid() = user_id);

create policy "recordings_delete_own" on public.recordings
  for delete using (auth.uid() = user_id);

create policy "recordings_service_all" on public.recordings
  for all using (auth.role() = 'service_role');

create trigger recordings_updated_at
  before update on public.recordings
  for each row execute function public.set_updated_at();
