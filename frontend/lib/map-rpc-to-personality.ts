/**
 * Maps Supabase RPC `get_website_data` JSON to the PersonalitySchema used by layouts and CV/Dating pages.
 */

import type {
  ColorPalette,
  CVContent,
  DatingContent,
  GetWebsiteDataRPCResponse,
  LayoutDirectives,
  PersonaBlend,
  PersonaType,
  PersonalityDimensions,
  PersonalitySchema,
  TypographyConfig,
  WebsiteConfig,
  WorkExperience,
} from "@/types/personality-schema";

const PERSONAS: PersonaType[] = [
  "minimalist-refined",
  "maximalist-bold",
  "organic-warm",
  "structured-professional",
];

function asPersona(v: string | null | undefined): PersonaType {
  if (v && PERSONAS.includes(v as PersonaType)) return v as PersonaType;
  return "structured-professional";
}

function weightFromDb(
  w: string | number | null | undefined,
  fallback: number,
): number {
  if (typeof w === "number" && !Number.isNaN(w)) return w;
  if (w === "light") return 300;
  if (w === "bold") return 700;
  if (w === "regular") return 400;
  return fallback;
}

function typographyFromRpc(p: GetWebsiteDataRPCResponse["personality"]): TypographyConfig {
  const displayKey = String(p.typography_display ?? "modern-sans");
  const bodyKey = String(p.typography_body ?? "modern-sans");
  const displayMap: Record<string, string> = {
    serif: "Playfair Display",
    geometric: "Outfit",
    humanist: "Source Serif 4",
    "modern-sans": "Inter",
  };
  const tw = p.typography_weight as string | number | undefined;
  return {
    display_font: displayMap[displayKey] ?? displayMap["modern-sans"],
    body_font: displayMap[bodyKey] ?? displayMap["modern-sans"],
    scale_ratio: 1.333,
    weight_display: weightFromDb(tw, 600),
    weight_body: weightFromDb(tw, 400),
  };
}

function defaultPalette(accent: string): ColorPalette {
  return {
    primary: "#0f172a",
    secondary: "#64748b",
    accent: accent || "#6366f1",
    background: "#f8fafc",
    surface: "#ffffff",
    text_primary: "#0f172a",
    text_secondary: "#64748b",
    border: "#e2e8f0",
  };
}

function emptyCv(): CVContent {
  return {
    headline: "",
    positioning_statement: "",
    summary: "",
    work_history: [],
    skills: [],
    education: [],
    languages: [],
  };
}

function normalizeCv(raw: unknown): CVContent {
  if (!raw || typeof raw !== "object") return emptyCv();
  const r = raw as Record<string, unknown>;
  const positioning_statement =
    typeof r.positioning_statement === "string"
      ? r.positioning_statement
      : typeof r.positioning === "string"
        ? r.positioning
        : "";
  let work_history: WorkExperience[] = Array.isArray(r.work_history)
    ? (r.work_history as WorkExperience[])
    : [];
  if (work_history.length === 0 && Array.isArray(r.experience)) {
    work_history = (r.experience as Record<string, unknown>[]).map((e) => ({
      company: String(e.company ?? ""),
      role: String(e.role ?? ""),
      start_date: String(e.start_date ?? ""),
      end_date: e.end_date != null ? String(e.end_date) : null,
      description: String(e.summary ?? e.description ?? ""),
      achievements: Array.isArray(e.achievements)
        ? (e.achievements as string[])
        : [],
      location: e.location != null ? String(e.location) : null,
    }));
  }
  const skills = Array.isArray(r.skills)
    ? (r.skills as string[]).map(String)
    : [];
  return {
    headline: typeof r.headline === "string" ? r.headline : "",
    positioning_statement,
    summary: typeof r.summary === "string" ? r.summary : "",
    work_history,
    skills,
    education: Array.isArray(r.education) ? (r.education as CVContent["education"]) : [],
    languages: Array.isArray(r.languages) ? (r.languages as CVContent["languages"]) : [],
  };
}

function emptyDating(): DatingContent {
  return {
    tagline: "",
    intro: "",
    values: [],
    looking_for: [],
    personality_tagline: "",
    interests: [],
    ambition_score: 5,
    adventure_score: 5,
  };
}

function normalizeDating(raw: unknown): DatingContent {
  if (!raw || typeof raw !== "object") return emptyDating();
  const r = raw as Record<string, unknown>;
  const intro =
    typeof r.intro === "string"
      ? r.intro
      : typeof r.about === "string"
        ? r.about
        : "";
  let looking_for: string[] = [];
  if (Array.isArray(r.looking_for)) looking_for = (r.looking_for as unknown[]).map(String);
  else if (typeof r.looking_for === "string") looking_for = [r.looking_for];
  return {
    tagline: typeof r.tagline === "string" ? r.tagline : "",
    intro,
    values: Array.isArray(r.values) ? (r.values as string[]).map(String) : [],
    looking_for,
    personality_tagline:
      typeof r.personality_tagline === "string" ? r.personality_tagline : "",
    interests: Array.isArray(r.interests) ? (r.interests as string[]).map(String) : [],
    ambition_score: typeof r.ambition_score === "number" ? r.ambition_score : 5,
    adventure_score: typeof r.adventure_score === "number" ? r.adventure_score : 5,
  };
}

function deriveWebsiteMode(
  configs: GetWebsiteDataRPCResponse["website_configs"],
  modesUnlocked: string[],
): WebsiteConfig {
  const list = Array.isArray(configs)
    ? configs.filter((c): c is NonNullable<typeof c> => c != null && typeof c === "object")
    : [];
  const pub = list.filter((c) => c.is_published);
  const hasCv = pub.some((c) => c.mode === "cv");
  const hasDating = pub.some((c) => c.mode === "dating");
  const unlockDating = modesUnlocked.includes("dating");

  let mode: WebsiteConfig["mode"] = "cv";
  if (unlockDating && hasCv && hasDating) mode = "both";
  else if (unlockDating && hasDating && !hasCv) mode = "dating";

  const default_mode: "cv" | "dating" =
    mode === "dating" ? "dating" : "cv";

  return {
    mode,
    default_mode,
    calendly_url: null,
    custom_domain: null,
    show_personality_insights: true,
    show_voice_clips: true,
    show_photo_reel: true,
  };
}

export function mapRpcToPersonalitySchema(
  data: GetWebsiteDataRPCResponse,
): PersonalitySchema {
  const u = data.user;
  const p = data.personality;

  const dimensions: PersonalityDimensions = {
    warmth: Number(p.dim_warmth),
    energy: Number(p.dim_energy),
    confidence: Number(p.dim_confidence),
    curiosity: Number(p.dim_curiosity),
    formality: Number(p.dim_formality),
    humor: Number(p.dim_humor),
    openness: Number(p.dim_openness),
  };

  const secondary = p.secondary_persona
    ? asPersona(p.secondary_persona)
    : null;
  const persona_blend: PersonaBlend = {
    primary: asPersona(p.primary_persona),
    primary_weight: Number(p.primary_weight),
    secondary,
    secondary_weight: secondary ? Number(p.secondary_weight) : 0,
  };

  const layout_directives: LayoutDirectives = {
    density: Number(p.layout_density),
    asymmetry: Number(p.layout_asymmetry),
    whitespace_ratio: Number(p.layout_whitespace),
    flow_direction: p.layout_flow as LayoutDirectives["flow_direction"],
  };

  const cv_content = normalizeCv(p.cv_content);
  const rawCv = p.cv_content as unknown;
  const calendlyFromCv =
    rawCv &&
    typeof rawCv === "object" &&
    typeof (rawCv as Record<string, unknown>).calendar_url === "string"
      ? String((rawCv as Record<string, unknown>).calendar_url)
      : null;

  const website_config = deriveWebsiteMode(
    data.website_configs,
    (u.modes_unlocked ?? []).map(String),
  );
  if (calendlyFromCv) {
    website_config.calendly_url = calendlyFromCv;
  }

  const accent =
    typeof p.color_accent === "string" && p.color_accent.startsWith("#")
      ? p.color_accent
      : "#6366f1";

  return {
    user_id: u.id,
    username: u.username,
    full_name: u.display_name?.trim() || u.username,
    avatar_url: u.avatar_url ?? null,
    schema_version: "1.0.0",
    generated_at: new Date().toISOString(),
    dimensions,
    persona_blend,
    layout_directives,
    typography: typographyFromRpc(p),
    color_palette: defaultPalette(accent),
    cv_content,
    dating_content: normalizeDating(p.dating_content),
    website_config,
  };
}
