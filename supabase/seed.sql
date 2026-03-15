-- Seed: demo user for development + founder's character website
-- Only runs locally (supabase db reset) or via `supabase db seed`

-- Insert demo auth user (local dev only)
insert into auth.users (
  id,
  email,
  encrypted_password,
  email_confirmed_at,
  created_at,
  updated_at,
  raw_app_meta_data,
  raw_user_meta_data,
  is_super_admin,
  role
) values (
  '00000000-0000-0000-0000-000000000001',
  'demo@characterwebsites.com',
  crypt('demo1234', gen_salt('bf')),
  now(),
  now(),
  now(),
  '{"provider":"email","providers":["email"]}',
  '{}',
  false,
  'authenticated'
) on conflict (id) do nothing;

-- Public user profile
insert into public.users (id, email, username, display_name, modes_unlocked)
values (
  '00000000-0000-0000-0000-000000000001',
  'demo@characterwebsites.com',
  'demo',
  'Demo User',
  '{cv, dating}'
) on conflict (id) do nothing;

-- Seed personality schema (balanced, Organic-Warm leaning)
insert into public.personality_schemas (
  id,
  user_id,
  version,
  is_current,
  dim_warmth, dim_energy, dim_confidence, dim_curiosity,
  dim_formality, dim_humor, dim_openness,
  primary_persona, primary_weight,
  secondary_persona, secondary_weight,
  color_temperature, color_saturation, color_accent,
  typography_display, typography_body, typography_weight,
  layout_density, layout_asymmetry, layout_whitespace, layout_flow,
  animation_speed, animation_intensity,
  cv_content,
  dating_content
) values (
  '00000000-0000-0000-0000-000000000010',
  '00000000-0000-0000-0000-000000000001',
  1,
  true,
  72, 65, 68, 81,
  40, 74, 78,
  'organic-warm', 65,
  'minimalist-refined', 35,
  'warm', 'medium', '#e07a5f',
  'humanist', 'humanist', 'regular',
  4, 3, 7, 'vertical',
  'medium', 'moderate',
  '{
    "headline": "Builder of things that matter",
    "positioning": "I turn fuzzy ideas into products people actually use. I believe the best work comes from understanding people deeply — not just their problems, but their character.",
    "experience": [
      {"role": "Founder", "company": "Character-Websites", "period": "2026 – present", "summary": "Building a platform that captures authentic personality through voice and translates it into living personal websites."},
      {"role": "Product Lead", "company": "Cittasana", "period": "2023 – 2026", "summary": "Led product development for wellness platform serving 50k+ users."}
    ],
    "skills": ["Product Strategy", "Python", "Next.js", "Claude AI", "User Research"],
    "calendar_url": "https://calendly.com/demo"
  }',
  '{
    "tagline": "Curious mind, warm heart",
    "about": "I get genuinely excited about ideas at 11pm and equally excited about good coffee at 7am. I think depth matters more than breadth, and I''d rather have one real conversation than ten surface ones.",
    "values": ["Authenticity over performance", "Depth over breadth", "Build things that last"],
    "looking_for": "Someone who reads books they didn''t have to, laughs at their own jokes, and means what they say."
  }'
) on conflict (id) do nothing;

-- Seed website configs
insert into public.website_configs (user_id, schema_id, mode, is_published)
values
  ('00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010', 'cv', true),
  ('00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000010', 'dating', true)
on conflict (user_id, mode) do nothing;

-- Seed sample voice clips metadata (no actual audio in seed)
insert into public.voice_clips (user_id, storage_path, title, description, duration_seconds, display_order, personality_tags)
values
  ('00000000-0000-0000-0000-000000000001', 'voice-clips/00000000-0000-0000-0000-000000000001/clip-1.mp3', 'On building things', 'Talking about what drives me to create', 42.5, 1, '{curiosity, energy, confidence}'),
  ('00000000-0000-0000-0000-000000000001', 'voice-clips/00000000-0000-0000-0000-000000000001/clip-2.mp3', 'What makes me laugh', 'A story about something that genuinely cracked me up', 28.0, 2, '{humor, warmth}'),
  ('00000000-0000-0000-0000-000000000001', 'voice-clips/00000000-0000-0000-0000-000000000001/clip-3.mp3', 'My morning ritual', 'How I start every day and why it matters', 35.5, 3, '{warmth, openness}')
on conflict do nothing;
