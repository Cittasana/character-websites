/**
 * TypeScript types for the Character-Websites Personality Schema.
 * Mirrors the JSON structure produced by the Claude AI analysis pipeline on the backend.
 *
 * Also mirrors the shape returned by the Supabase RPC `get_website_data(p_username)`,
 * which returns a nested object: { user, personality, website_configs }.
 */

// ── Core personality dimensions (0–100 scale, stored as dim_* in DB) ────────

export interface PersonalityDimensions {
  warmth: number;         // 0-100: cold/analytical → warm/empathetic
  energy: number;         // 0-100: calm/reserved → high-energy/expressive
  confidence: number;     // 0-100: humble/uncertain → bold/assured
  curiosity: number;      // 0-100: conventional → intellectually adventurous
  formality: number;      // 0-100: casual/relaxed → formal/professional
  humor: number;          // 0-100: serious → playful/funny
  openness: number;       // 0-100: private/guarded → open/transparent
}

// ── Persona blend ────────────────────────────────────────────────────────────

export type PersonaType =
  | "minimalist-refined"
  | "maximalist-bold"
  | "organic-warm"
  | "structured-professional";

export interface PersonaBlend {
  primary: PersonaType;
  primary_weight: number;       // 0-100
  secondary: PersonaType | null;
  secondary_weight: number;     // 0-100 (primary_weight + secondary_weight = 100)
}

// ── Layout directives ────────────────────────────────────────────────────────

export type FlowDirection = "vertical" | "horizontal" | "diagonal";

export interface LayoutDirectives {
  density: number;              // 1-10: sparse → dense
  asymmetry: number;            // 1-10: centered → offset
  whitespace_ratio: number;     // 1-10: compressed → generous whitespace
  flow_direction: FlowDirection;
}

// ── Typography ───────────────────────────────────────────────────────────────

export interface TypographyConfig {
  display_font: string;         // Google Fonts name or system font
  body_font: string;
  scale_ratio: number;          // 1.0-1.8: type scale multiplier
  weight_display: number;       // 100-900
  weight_body: number;
}

// ── Color palette ────────────────────────────────────────────────────────────

export interface ColorPalette {
  primary: string;              // hex color
  secondary: string;            // hex color
  accent: string;               // hex color
  background: string;           // hex color
  surface: string;              // hex color
  text_primary: string;         // hex color
  text_secondary: string;       // hex color
  border: string;               // hex color
}

// ── CV content ───────────────────────────────────────────────────────────────

export interface WorkExperience {
  company: string;
  role: string;
  start_date: string;           // ISO date string
  end_date: string | null;      // null = present
  description: string;
  achievements: string[];
  location: string | null;
}

export interface CVContent {
  headline: string;             // Professional tagline
  positioning_statement: string; // Personality-driven professional statement
  summary: string;              // Short professional summary
  work_history: WorkExperience[];
  skills: string[];
  education: {
    institution: string;
    degree: string;
    field: string;
    year: number | null;
  }[];
  languages: {
    language: string;
    level: string;
  }[];
}

// ── Dating content ───────────────────────────────────────────────────────────

export interface DatingContent {
  tagline: string;              // Dating profile headline
  intro: string;                // Opening hook
  values: string[];             // What they believe in
  looking_for: string[];        // What they want in a partner
  personality_tagline: string;  // Short character description
  interests: string[];
  ambition_score: number;       // 0-10
  adventure_score: number;      // 0-10
}

// ── Voice clips ──────────────────────────────────────────────────────────────

export interface VoiceClip {
  id: string;
  label: string;                // Human-readable clip label
  duration_seconds: number;
  signed_url: string;           // Temporary S3 signed URL
  expires_at: string;           // ISO timestamp
  waveform_data: number[] | null; // Pre-computed amplitude array (0-1)
}

// ── Photos ───────────────────────────────────────────────────────────────────

export interface Photo {
  id: string;
  signed_url: string;
  expires_at: string;
  alt_text: string | null;
  is_primary: boolean;
  order: number;
}

// ── Website config ───────────────────────────────────────────────────────────

export interface WebsiteConfig {
  mode: "cv" | "dating" | "both";
  default_mode: "cv" | "dating";
  calendly_url: string | null;
  custom_domain: string | null;
  show_personality_insights: boolean;
  show_voice_clips: boolean;
  show_photo_reel: boolean;
}

// ── Root schema ──────────────────────────────────────────────────────────────

export interface PersonalitySchema {
  // Identity
  user_id: string;
  username: string;             // subdomain slug
  full_name: string;
  avatar_url: string | null;    // S3 signed URL for primary photo
  schema_version: string;       // e.g. "1.0.0"
  generated_at: string;         // ISO timestamp

  // Personality
  dimensions: PersonalityDimensions;
  persona_blend: PersonaBlend;
  layout_directives: LayoutDirectives;
  typography: TypographyConfig;
  color_palette: ColorPalette;

  // Content
  cv_content: CVContent;
  dating_content: DatingContent;
  website_config: WebsiteConfig;

  // Media (populated separately from /api/retrieve endpoints)
  voice_clips?: VoiceClip[];
  photos?: Photo[];
}

// ── RPC response shape (get_website_data) ────────────────────────────────────
//
// The Supabase RPC `get_website_data(p_username)` returns a flat JSONB object
// with a DIFFERENT shape than PersonalitySchema. The frontend api.server.ts casts
// the RPC result directly to PersonalitySchema, but the actual RPC returns nested
// { user, personality, website_configs } objects.
//
// Use GetWebsiteDataRPCResponse as the actual RPC return type, then map to
// PersonalitySchema for rendering.

export interface RPCUserData {
  id: string;
  username: string;
  display_name: string | null;
  avatar_url: string | null;
  modes_unlocked: string[];
}

export interface RPCPersonalityData {
  // Dimensions (stored as 0-100 in DB, prefixed dim_*)
  dim_warmth: number;
  dim_energy: number;
  dim_confidence: number;
  dim_curiosity: number;
  dim_formality: number;
  dim_humor: number;
  dim_openness: number;

  // Persona
  primary_persona: PersonaType;
  primary_weight: number;
  secondary_persona: PersonaType | null;
  secondary_weight: number;

  // Color system
  color_temperature: number;
  color_saturation: number;
  color_accent: string;

  // Typography
  typography_display: string;
  typography_body: string;
  typography_weight: number;

  // Layout
  layout_density: number;
  layout_asymmetry: number;
  layout_whitespace: number;
  layout_flow: FlowDirection;

  // Animation
  animation_speed: number;
  animation_intensity: number;

  // Content (stored as JSONB)
  cv_content: CVContent | null;
  dating_content: DatingContent | null;
}

export interface RPCWebsiteConfigEntry {
  mode: "cv" | "dating" | "both";
  is_published: boolean;
  last_rendered_at: string | null;
}

export interface GetWebsiteDataRPCResponse {
  user: RPCUserData;
  personality: RPCPersonalityData;
  website_configs: RPCWebsiteConfigEntry[] | null;
}

// ── API response wrappers ────────────────────────────────────────────────────

export interface ApiResponse<T> {
  data: T;
  success: boolean;
  error?: string;
}

export interface VoiceClipsResponse {
  clips: VoiceClip[];
  user_id: string;
}

export interface QARequest {
  user_id: string;
  question: string;
  mode: "cv" | "dating";
}

export interface QAResponse {
  answer: string;
  audio_url: string | null;     // Signed S3 URL for synthesized audio
  audio_expires_at: string | null;
}
