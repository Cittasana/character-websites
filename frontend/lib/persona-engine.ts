/**
 * Persona Engine
 *
 * Derives the active rendering configuration from a PersonalitySchema.
 * Used by layout components and animation providers to determine behavior.
 */

import type {
  PersonalitySchema,
  PersonaType,
  PersonalityDimensions,
} from "@/types/personality-schema";

// ── Persona detection helpers ────────────────────────────────────────────────

export interface PersonaConfig {
  type: PersonaType;
  weight: number; // 0-100
}

export function getActivePersonas(schema: PersonalitySchema): PersonaConfig[] {
  const configs: PersonaConfig[] = [
    { type: schema.persona_blend.primary, weight: schema.persona_blend.primary_weight },
  ];

  if (schema.persona_blend.secondary && schema.persona_blend.secondary_weight > 0) {
    configs.push({
      type: schema.persona_blend.secondary,
      weight: schema.persona_blend.secondary_weight,
    });
  }

  return configs;
}

export function getPrimaryPersona(schema: PersonalitySchema): PersonaType {
  return schema.persona_blend.primary;
}

// ── Animation configuration ──────────────────────────────────────────────────

export interface AnimationConfig {
  /** Initial fade-in duration in seconds */
  fadeInDuration: number;
  /** Stagger delay between child elements in seconds */
  staggerDelay: number;
  /** Whether parallax scrolling effects should be active */
  enableParallax: boolean;
  /** Whether hover scale effects should be applied */
  hoverScale: number;
  /** Spring config for Framer Motion */
  spring: { type: "spring"; stiffness: number; damping: number; mass: number };
  /** Tween config for Framer Motion */
  tween: { type: "tween"; duration: number; ease: string };
}

const personaAnimationDefaults: Record<PersonaType, AnimationConfig> = {
  "minimalist-refined": {
    fadeInDuration: 0.9,
    staggerDelay: 0.12,
    enableParallax: false,
    hoverScale: 1.01,
    spring: { type: "spring", stiffness: 80, damping: 30, mass: 1 },
    tween: { type: "tween", duration: 0.7, ease: "easeOut" },
  },
  "maximalist-bold": {
    fadeInDuration: 0.2,
    staggerDelay: 0.04,
    enableParallax: true,
    hoverScale: 1.05,
    spring: { type: "spring", stiffness: 400, damping: 20, mass: 0.8 },
    tween: { type: "tween", duration: 0.18, ease: "easeIn" },
  },
  "organic-warm": {
    fadeInDuration: 0.6,
    staggerDelay: 0.09,
    enableParallax: false,
    hoverScale: 1.03,
    spring: { type: "spring", stiffness: 200, damping: 20, mass: 1.2 },
    tween: { type: "tween", duration: 0.5, ease: "easeInOut" },
  },
  "structured-professional": {
    fadeInDuration: 0.4,
    staggerDelay: 0.06,
    enableParallax: false,
    hoverScale: 1.02,
    spring: { type: "spring", stiffness: 300, damping: 28, mass: 1 },
    tween: { type: "tween", duration: 0.3, ease: "easeOut" },
  },
};

function interpolateAnimationConfig(
  primary: AnimationConfig,
  secondary: AnimationConfig,
  t: number,
): AnimationConfig {
  const lerp = (a: number, b: number) => a + (b - a) * t;
  return {
    fadeInDuration: lerp(primary.fadeInDuration, secondary.fadeInDuration),
    staggerDelay: lerp(primary.staggerDelay, secondary.staggerDelay),
    enableParallax: t > 0.5 ? secondary.enableParallax : primary.enableParallax,
    hoverScale: lerp(primary.hoverScale, secondary.hoverScale),
    spring: t > 0.5 ? secondary.spring : primary.spring,
    tween: t > 0.5 ? secondary.tween : primary.tween,
  };
}

export function getAnimationConfig(schema: PersonalitySchema): AnimationConfig {
  const primary = personaAnimationDefaults[schema.persona_blend.primary];
  const secondary = schema.persona_blend.secondary
    ? personaAnimationDefaults[schema.persona_blend.secondary]
    : null;

  if (!secondary || schema.persona_blend.secondary_weight === 0) {
    return primary;
  }

  return interpolateAnimationConfig(
    primary,
    secondary,
    schema.persona_blend.secondary_weight / 100,
  );
}

// ── Layout mode helpers ──────────────────────────────────────────────────────

export interface LayoutMode {
  isAsymmetric: boolean;
  isDense: boolean;
  isSparse: boolean;
  gridCols: "1" | "2" | "3" | "4" | "6" | "12";
  sectionVariant: "stacked" | "split" | "overlapping";
  heroVariant: "centered" | "left-aligned" | "full-bleed";
  cardVariant: "flat" | "raised" | "bordered" | "ghost";
}

export function getLayoutMode(
  schema: PersonalitySchema,
): LayoutMode {
  const { layout_directives, persona_blend } = schema;
  const { density, asymmetry } = layout_directives;

  const cols: LayoutMode["gridCols"] =
    density <= 2 ? "1"
    : density <= 4 ? "2"
    : density <= 6 ? "3"
    : density <= 8 ? "4"
    : "6";

  const sectionVariant: LayoutMode["sectionVariant"] =
    persona_blend.primary === "maximalist-bold" ? "overlapping"
    : asymmetry > 6 ? "split"
    : "stacked";

  const heroVariant: LayoutMode["heroVariant"] =
    persona_blend.primary === "minimalist-refined" ? "centered"
    : asymmetry > 5 ? "left-aligned"
    : "centered";

  const cardVariant: LayoutMode["cardVariant"] =
    persona_blend.primary === "minimalist-refined" ? "flat"
    : persona_blend.primary === "maximalist-bold" ? "raised"
    : persona_blend.primary === "structured-professional" ? "bordered"
    : "ghost";

  return {
    isAsymmetric: asymmetry > 5,
    isDense: density > 6,
    isSparse: density < 4,
    gridCols: cols,
    sectionVariant,
    heroVariant,
    cardVariant,
  };
}

// ── Personality dimension → visual indicator ─────────────────────────────────

export interface DimensionVisual {
  label: string;
  value: number;        // 0-10
  icon: string;
  lowLabel: string;
  highLabel: string;
  accentIndex: number;  // 0-6 for color cycling
}

export function getDimensionVisuals(
  dimensions: PersonalityDimensions,
): DimensionVisual[] {
  return [
    {
      label: "Warmth",
      value: dimensions.warmth,
      icon: "🌡",
      lowLabel: "Analytical",
      highLabel: "Warm",
      accentIndex: 0,
    },
    {
      label: "Energy",
      value: dimensions.energy,
      icon: "⚡",
      lowLabel: "Calm",
      highLabel: "High-energy",
      accentIndex: 1,
    },
    {
      label: "Confidence",
      value: dimensions.confidence,
      icon: "◈",
      lowLabel: "Humble",
      highLabel: "Bold",
      accentIndex: 2,
    },
    {
      label: "Curiosity",
      value: dimensions.curiosity,
      icon: "◎",
      lowLabel: "Conventional",
      highLabel: "Adventurous",
      accentIndex: 3,
    },
    {
      label: "Formality",
      value: dimensions.formality,
      icon: "◻",
      lowLabel: "Casual",
      highLabel: "Formal",
      accentIndex: 4,
    },
    {
      label: "Humor",
      value: dimensions.humor,
      icon: "◑",
      lowLabel: "Serious",
      highLabel: "Playful",
      accentIndex: 5,
    },
    {
      label: "Openness",
      value: dimensions.openness,
      icon: "◯",
      lowLabel: "Private",
      highLabel: "Open",
      accentIndex: 6,
    },
  ];
}

// ── Mode resolution ──────────────────────────────────────────────────────────

export type SiteMode = "cv" | "dating";

export function resolveMode(
  schema: PersonalitySchema,
  requested: string | undefined | null,
): SiteMode {
  const config = schema.website_config;

  if (config.mode === "cv") return "cv";
  if (config.mode === "dating") return "dating";

  // mode === "both"
  if (requested === "dating" || requested === "cv") return requested;
  return config.default_mode;
}
