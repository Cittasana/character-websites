-- User photos for avatar generation and personality analysis
create table public.photos (
  id              uuid primary key default gen_random_uuid(),
  user_id         uuid not null references public.users(id) on delete cascade,
  storage_path    text not null,               -- Supabase Storage: user-photos/{user_id}/{filename}
  original_filename text,
  file_size_bytes bigint,
  mime_type       text not null default 'image/jpeg',
  width_px        integer,
  height_px       integer,
  is_primary      boolean not null default false,  -- used as main avatar
  analysis_result jsonb,                       -- Claude visual analysis output
  processing_status text not null default 'pending'
    check (processing_status in ('pending', 'processing', 'complete', 'failed')),
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);

create index photos_user_id_idx on public.photos (user_id);
create index photos_primary_idx on public.photos (user_id, is_primary) where is_primary = true;

alter table public.photos enable row level security;

create policy "photos_select_own" on public.photos
  for select using (auth.uid() = user_id);

create policy "photos_insert_own" on public.photos
  for insert with check (auth.uid() = user_id);

create policy "photos_update_own" on public.photos
  for update using (auth.uid() = user_id);

create policy "photos_delete_own" on public.photos
  for delete using (auth.uid() = user_id);

create policy "photos_service_all" on public.photos
  for all using (auth.role() = 'service_role');

create trigger photos_updated_at
  before update on public.photos
  for each row execute function public.set_updated_at();
