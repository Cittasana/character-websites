-- Users table (extends Supabase auth.users)
create table public.users (
  id            uuid primary key references auth.users(id) on delete cascade,
  email         text unique not null,
  username      text unique not null,           -- becomes the subdomain: username.characterwebsites.com
  display_name  text,
  avatar_url    text,
  subscription_status text not null default 'active' check (subscription_status in ('active', 'suspended', 'cancelled')),
  modes_unlocked text[] not null default '{cv}', -- e.g. '{cv, dating}'
  omi_device_id text,
  omi_access_token text,                        -- encrypted at rest via Supabase Vault in production
  last_sync_at  timestamptz,
  sync_enabled  boolean not null default true,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

-- Index for subdomain lookups (hot path)
create index users_username_idx on public.users (username);

alter table public.users enable row level security;

-- Users can only read/update their own row
create policy "users_select_own" on public.users
  for select using (auth.uid() = id);

create policy "users_update_own" on public.users
  for update using (auth.uid() = id);

-- Service role can do everything (for backend workers)
create policy "users_service_all" on public.users
  for all using (auth.role() = 'service_role');

-- Trigger: keep updated_at current
create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger users_updated_at
  before update on public.users
  for each row execute function public.set_updated_at();
