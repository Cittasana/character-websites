-- Immutable audit log for all data ingest events
create table public.audit_logs (
  id              uuid primary key default gen_random_uuid(),
  user_id         uuid references public.users(id) on delete set null,
  event_type      text not null,               -- e.g. 'voice_upload', 'photo_upload', 'analysis_complete'
  resource_type   text,                        -- e.g. 'recording', 'photo', 'personality_schema'
  resource_id     uuid,
  ip_address      inet,
  user_agent      text,
  request_id      text,
  metadata        jsonb not null default '{}',
  success         boolean not null default true,
  error_message   text,
  created_at      timestamptz not null default now()
);

-- Partition by month for query performance at scale
create index audit_logs_user_id_idx on public.audit_logs (user_id);
create index audit_logs_event_type_idx on public.audit_logs (event_type);
create index audit_logs_created_at_idx on public.audit_logs (created_at desc);

alter table public.audit_logs enable row level security;

-- Users can read their own audit log
create policy "audit_logs_select_own" on public.audit_logs
  for select using (auth.uid() = user_id);

-- Only service role can insert (app layer cannot forge audit events)
create policy "audit_logs_insert_service" on public.audit_logs
  for insert with check (auth.role() = 'service_role');

-- No updates or deletes — immutable log
