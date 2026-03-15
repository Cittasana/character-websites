-- Curated voice clips selected for public display (dating mode)
create table public.voice_clips (
  id              uuid primary key default gen_random_uuid(),
  user_id         uuid not null references public.users(id) on delete cascade,
  recording_id    uuid references public.recordings(id) on delete set null,
  storage_path    text not null,               -- Supabase Storage: voice-clips/{user_id}/{filename}
  title           text,                        -- e.g. "Talking about travel"
  description     text,                        -- Claude-generated clip description
  duration_seconds float not null,
  display_order   smallint not null default 0,
  is_public       boolean not null default true,
  personality_tags text[],                     -- e.g. {humor, warmth, curiosity}
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);

create index voice_clips_user_id_idx on public.voice_clips (user_id, display_order);

alter table public.voice_clips enable row level security;

-- Public clips are readable by anyone (for dating mode)
create policy "voice_clips_select_public" on public.voice_clips
  for select using (is_public = true);

create policy "voice_clips_select_own" on public.voice_clips
  for select using (auth.uid() = user_id);

create policy "voice_clips_update_own" on public.voice_clips
  for update using (auth.uid() = user_id);

create policy "voice_clips_delete_own" on public.voice_clips
  for delete using (auth.uid() = user_id);

create policy "voice_clips_service_all" on public.voice_clips
  for all using (auth.role() = 'service_role');

create trigger voice_clips_updated_at
  before update on public.voice_clips
  for each row execute function public.set_updated_at();
