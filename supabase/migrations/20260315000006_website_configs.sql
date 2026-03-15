-- Current website configuration per user per mode
create table public.website_configs (
  id              uuid primary key default gen_random_uuid(),
  user_id         uuid not null references public.users(id) on delete cascade,
  schema_id       uuid references public.personality_schemas(id) on delete set null,
  mode            text not null default 'cv' check (mode in ('cv', 'dating')),
  is_published    boolean not null default true,
  custom_overrides jsonb not null default '{}',  -- user manual tweaks
  last_rendered_at timestamptz,
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now(),
  unique (user_id, mode)
);

create index website_configs_user_id_idx on public.website_configs (user_id);

alter table public.website_configs enable row level security;

-- Public read for website rendering
create policy "website_configs_select_public" on public.website_configs
  for select using (is_published = true);

create policy "website_configs_select_own" on public.website_configs
  for select using (auth.uid() = user_id);

create policy "website_configs_update_own" on public.website_configs
  for update using (auth.uid() = user_id);

create policy "website_configs_service_all" on public.website_configs
  for all using (auth.role() = 'service_role');

create trigger website_configs_updated_at
  before update on public.website_configs
  for each row execute function public.set_updated_at();
