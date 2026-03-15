-- Helper: get current personality schema for a user by username (used by frontend subdomain routing)
create or replace function public.get_website_data(p_username text)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  v_user_id uuid;
  v_result jsonb;
begin
  select id into v_user_id
  from public.users
  where username = p_username;

  if v_user_id is null then
    return null;
  end if;

  select jsonb_build_object(
    'user', jsonb_build_object(
      'id', u.id,
      'username', u.username,
      'display_name', u.display_name,
      'avatar_url', u.avatar_url,
      'modes_unlocked', u.modes_unlocked
    ),
    'personality', jsonb_build_object(
      'dim_warmth', ps.dim_warmth,
      'dim_energy', ps.dim_energy,
      'dim_confidence', ps.dim_confidence,
      'dim_curiosity', ps.dim_curiosity,
      'dim_formality', ps.dim_formality,
      'dim_humor', ps.dim_humor,
      'dim_openness', ps.dim_openness,
      'primary_persona', ps.primary_persona,
      'primary_weight', ps.primary_weight,
      'secondary_persona', ps.secondary_persona,
      'secondary_weight', ps.secondary_weight,
      'color_temperature', ps.color_temperature,
      'color_saturation', ps.color_saturation,
      'color_accent', ps.color_accent,
      'typography_display', ps.typography_display,
      'typography_body', ps.typography_body,
      'typography_weight', ps.typography_weight,
      'layout_density', ps.layout_density,
      'layout_asymmetry', ps.layout_asymmetry,
      'layout_whitespace', ps.layout_whitespace,
      'layout_flow', ps.layout_flow,
      'animation_speed', ps.animation_speed,
      'animation_intensity', ps.animation_intensity,
      'cv_content', ps.cv_content,
      'dating_content', ps.dating_content
    ),
    'website_configs', jsonb_agg(
      jsonb_build_object(
        'mode', wc.mode,
        'is_published', wc.is_published,
        'last_rendered_at', wc.last_rendered_at
      )
    )
  ) into v_result
  from public.users u
  join public.personality_schemas ps on ps.user_id = u.id and ps.is_current = true
  left join public.website_configs wc on wc.user_id = u.id and wc.is_published = true
  where u.id = v_user_id
  group by u.id, u.username, u.display_name, u.avatar_url, u.modes_unlocked,
           ps.dim_warmth, ps.dim_energy, ps.dim_confidence, ps.dim_curiosity,
           ps.dim_formality, ps.dim_humor, ps.dim_openness,
           ps.primary_persona, ps.primary_weight, ps.secondary_persona, ps.secondary_weight,
           ps.color_temperature, ps.color_saturation, ps.color_accent,
           ps.typography_display, ps.typography_body, ps.typography_weight,
           ps.layout_density, ps.layout_asymmetry, ps.layout_whitespace, ps.layout_flow,
           ps.animation_speed, ps.animation_intensity, ps.cv_content, ps.dating_content;

  return v_result;
end;
$$;

-- Helper: mark new schema as current, retire previous
create or replace function public.set_current_personality_schema(p_schema_id uuid)
returns void
language plpgsql
security definer
set search_path = public
as $$
declare
  v_user_id uuid;
begin
  select user_id into v_user_id from public.personality_schemas where id = p_schema_id;

  -- Retire all previous current schemas for this user
  update public.personality_schemas
  set is_current = false
  where user_id = v_user_id and is_current = true;

  -- Set new current
  update public.personality_schemas
  set is_current = true
  where id = p_schema_id;
end;
$$;

-- Helper: increment schema version
create or replace function public.next_schema_version(p_user_id uuid)
returns integer
language sql
security definer
set search_path = public
as $$
  select coalesce(max(version), 0) + 1
  from public.personality_schemas
  where user_id = p_user_id;
$$;
