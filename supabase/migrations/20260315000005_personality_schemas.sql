-- Versioned personality schema output from Claude analysis
create table public.personality_schemas (
  id              uuid primary key default gen_random_uuid(),
  user_id         uuid not null references public.users(id) on delete cascade,
  version         integer not null default 1,
  is_current      boolean not null default false,

  -- 7 personality dimensions (0-100)
  dim_warmth      smallint not null default 50 check (dim_warmth between 0 and 100),
  dim_energy      smallint not null default 50 check (dim_energy between 0 and 100),
  dim_confidence  smallint not null default 50 check (dim_confidence between 0 and 100),
  dim_curiosity   smallint not null default 50 check (dim_curiosity between 0 and 100),
  dim_formality   smallint not null default 50 check (dim_formality between 0 and 100),
  dim_humor       smallint not null default 50 check (dim_humor between 0 and 100),
  dim_openness    smallint not null default 50 check (dim_openness between 0 and 100),

  -- Persona blend
  primary_persona       text not null default 'structured-professional'
    check (primary_persona in ('minimalist-refined', 'maximalist-bold', 'organic-warm', 'structured-professional')),
  primary_weight        smallint not null default 70 check (primary_weight between 0 and 100),
  secondary_persona     text
    check (secondary_persona in ('minimalist-refined', 'maximalist-bold', 'organic-warm', 'structured-professional')),
  secondary_weight      smallint not null default 30 check (secondary_weight between 0 and 100),

  -- Design directives (used by frontend token engine)
  color_temperature     text not null default 'neutral' check (color_temperature in ('warm', 'cool', 'neutral')),
  color_saturation      text not null default 'medium' check (color_saturation in ('high', 'medium', 'low')),
  color_accent          text not null default '#6366f1',  -- hex color
  typography_display    text not null default 'modern-sans'
    check (typography_display in ('serif', 'geometric', 'humanist', 'modern-sans')),
  typography_body       text not null default 'modern-sans'
    check (typography_body in ('serif', 'geometric', 'humanist', 'modern-sans')),
  typography_weight     text not null default 'regular' check (typography_weight in ('light', 'regular', 'bold')),
  layout_density        smallint not null default 5 check (layout_density between 1 and 10),
  layout_asymmetry      smallint not null default 3 check (layout_asymmetry between 1 and 10),
  layout_whitespace     smallint not null default 5 check (layout_whitespace between 1 and 10),
  layout_flow           text not null default 'vertical' check (layout_flow in ('vertical', 'horizontal', 'diagonal')),
  animation_speed       text not null default 'medium' check (animation_speed in ('slow', 'medium', 'fast')),
  animation_intensity   text not null default 'moderate' check (animation_intensity in ('subtle', 'moderate', 'pronounced')),

  -- Mode-specific content (Claude-generated copy)
  cv_content      jsonb not null default '{}',
  dating_content  jsonb not null default '{}',

  -- pgvector embedding for semantic similarity / evolution tracking
  embedding       vector(1536),

  -- Source recordings used for this analysis
  source_recording_ids uuid[],
  recordings_count     integer not null default 0,

  claude_model    text not null default 'claude-sonnet-4-20250514',
  created_at      timestamptz not null default now()
);

create index personality_schemas_user_id_idx on public.personality_schemas (user_id);
create index personality_schemas_current_idx on public.personality_schemas (user_id, is_current) where is_current = true;
create index personality_schemas_embedding_idx on public.personality_schemas
  using hnsw (embedding vector_cosine_ops) with (m = 16, ef_construction = 64);

alter table public.personality_schemas enable row level security;

-- Public read for website rendering (frontend needs this without auth)
create policy "personality_schemas_select_public" on public.personality_schemas
  for select using (is_current = true);

create policy "personality_schemas_select_own_all" on public.personality_schemas
  for select using (auth.uid() = user_id);

create policy "personality_schemas_service_all" on public.personality_schemas
  for all using (auth.role() = 'service_role');

-- Only one current schema per user
create unique index personality_schemas_one_current_per_user
  on public.personality_schemas (user_id)
  where is_current = true;
