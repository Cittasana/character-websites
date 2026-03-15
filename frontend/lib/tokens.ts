/**
 * Design Token Architecture
 *
 * CSS custom properties are derived from the personality schema and injected
 * server-side as a <style> tag in the document <head>. This means every page
 * load serves uniquely computed tokens — zero flash of unstyled content.
 *
 * Token categories:
 *   --font-display, --font-body         → typography
 *   --color-primary, --color-accent...  → color palette
 *   --spacing-density, --gap-*          → layout density
 *   --radius-*                          → corner rounding
 *   --shadow-*                          → depth/elevation
 *   --motion-speed, --motion-easing     → animation timing
 *   --layout-columns, --layout-offset   → grid configuration
 */

import type {
  PersonalitySchema,
  PersonaBlend,
  PersonaType,
  LayoutDirectives,
  TypographyConfig,
  ColorPalette,
} from "@/types/personality-schema";

// ── Persona base token sets ──────────────────────────────────────────────────

interface PersonaTokenSet {
  // Typography
  fontDisplay: string;
  fontBody: string;
  fontWeightDisplay: number;
  fontWeightBody: number;
  typeScale: number;

  // Colors (will be overridden by schema palette, these are persona defaults)
  colorPrimary: string;
  colorSecondary: string;
  colorAccent: string;
  colorBackground: string;
  colorSurface: string;
  colorTextPrimary: string;
  colorTextSecondary: string;
  colorBorder: string;

  // Spacing
  spacingBase: number;    // rem, base spacing unit
  gapSm: number;
  gapMd: number;
  gapLg: number;

  // Borders
  radiusSm: number;       // px
  radiusMd: number;
  radiusLg: number;
  radiusFull: number;

  // Shadows
  shadowSm: string;
  shadowMd: string;
  shadowLg: string;

  // Motion
  motionSpeedFast: number;   // ms
  motionSpeedMed: number;
  motionSpeedSlow: number;
  motionEasing: string;

  // Layout
  layoutColumns: number;
  layoutOffset: string;       // CSS value: "0" = centered, positive = right-shifted
  sectionPaddingY: number;    // rem
}

const personaTokens: Record<PersonaType, PersonaTokenSet> = {
  "minimalist-refined": {
    fontDisplay: "'Playfair Display', 'EB Garamond', Georgia, serif",
    fontBody: "'Inter', 'Helvetica Neue', Arial, sans-serif",
    fontWeightDisplay: 400,
    fontWeightBody: 300,
    typeScale: 1.333,
    colorPrimary: "#1a1a1a",
    colorSecondary: "#666666",
    colorAccent: "#c9a96e",
    colorBackground: "#fafafa",
    colorSurface: "#ffffff",
    colorTextPrimary: "#1a1a1a",
    colorTextSecondary: "#666666",
    colorBorder: "#e5e5e5",
    spacingBase: 1.0,
    gapSm: 1.5,
    gapMd: 3.0,
    gapLg: 6.0,
    radiusSm: 0,
    radiusMd: 2,
    radiusLg: 4,
    radiusFull: 4,
    shadowSm: "none",
    shadowMd: "0 1px 3px rgba(0,0,0,0.06)",
    shadowLg: "0 2px 8px rgba(0,0,0,0.08)",
    motionSpeedFast: 400,
    motionSpeedMed: 600,
    motionSpeedSlow: 900,
    motionEasing: "cubic-bezier(0.4, 0, 0.2, 1)",
    layoutColumns: 1,
    layoutOffset: "0",
    sectionPaddingY: 8.0,
  },

  "maximalist-bold": {
    fontDisplay: "'Bebas Neue', 'Impact', sans-serif",
    fontBody: "'Oswald', 'Arial Black', sans-serif",
    fontWeightDisplay: 700,
    fontWeightBody: 700,
    typeScale: 1.618,
    colorPrimary: "#ff2d00",
    colorSecondary: "#0047ff",
    colorAccent: "#ffcc00",
    colorBackground: "#0a0a0a",
    colorSurface: "#1a1a1a",
    colorTextPrimary: "#ffffff",
    colorTextSecondary: "#cccccc",
    colorBorder: "#333333",
    spacingBase: 0.75,
    gapSm: 0.75,
    gapMd: 1.5,
    gapLg: 3.0,
    radiusSm: 0,
    radiusMd: 0,
    radiusLg: 0,
    radiusFull: 0,
    shadowSm: "4px 4px 0 rgba(255,45,0,0.5)",
    shadowMd: "6px 6px 0 rgba(255,45,0,0.5)",
    shadowLg: "8px 8px 0 rgba(255,45,0,0.8)",
    motionSpeedFast: 150,
    motionSpeedMed: 200,
    motionSpeedSlow: 350,
    motionEasing: "cubic-bezier(0.25, 0.46, 0.45, 0.94)",
    layoutColumns: 12,
    layoutOffset: "0",
    sectionPaddingY: 3.0,
  },

  "organic-warm": {
    fontDisplay: "'Nunito', 'Lato', sans-serif",
    fontBody: "'Nunito', 'Lato', sans-serif",
    fontWeightDisplay: 700,
    fontWeightBody: 400,
    typeScale: 1.25,
    colorPrimary: "#c4704a",
    colorSecondary: "#7d9b76",
    colorAccent: "#e8b89a",
    colorBackground: "#fdf6f0",
    colorSurface: "#fff9f5",
    colorTextPrimary: "#3d2c1e",
    colorTextSecondary: "#7a6155",
    colorBorder: "#e8d5c4",
    spacingBase: 1.0,
    gapSm: 1.25,
    gapMd: 2.5,
    gapLg: 5.0,
    radiusSm: 12,
    radiusMd: 20,
    radiusLg: 32,
    radiusFull: 9999,
    shadowSm: "0 2px 8px rgba(196,112,74,0.12)",
    shadowMd: "0 4px 16px rgba(196,112,74,0.16)",
    shadowLg: "0 8px 32px rgba(196,112,74,0.20)",
    motionSpeedFast: 300,
    motionSpeedMed: 500,
    motionSpeedSlow: 700,
    motionEasing: "cubic-bezier(0.34, 1.56, 0.64, 1)",
    layoutColumns: 2,
    layoutOffset: "0",
    sectionPaddingY: 5.0,
  },

  "structured-professional": {
    fontDisplay: "'DM Sans', 'Work Sans', system-ui, sans-serif",
    fontBody: "'DM Sans', 'Work Sans', system-ui, sans-serif",
    fontWeightDisplay: 700,
    fontWeightBody: 400,
    typeScale: 1.2,
    colorPrimary: "#0f2a4a",
    colorSecondary: "#2c3e50",
    colorAccent: "#2563eb",
    colorBackground: "#ffffff",
    colorSurface: "#f8fafc",
    colorTextPrimary: "#1e293b",
    colorTextSecondary: "#64748b",
    colorBorder: "#e2e8f0",
    spacingBase: 1.0,
    gapSm: 1.0,
    gapMd: 2.0,
    gapLg: 4.0,
    radiusSm: 4,
    radiusMd: 8,
    radiusLg: 12,
    radiusFull: 6,
    shadowSm: "0 1px 2px rgba(15,42,74,0.08)",
    shadowMd: "0 2px 8px rgba(15,42,74,0.10)",
    shadowLg: "0 4px 16px rgba(15,42,74,0.12)",
    motionSpeedFast: 200,
    motionSpeedMed: 300,
    motionSpeedSlow: 500,
    motionEasing: "cubic-bezier(0.4, 0, 0.2, 1)",
    layoutColumns: 3,
    layoutOffset: "0",
    sectionPaddingY: 4.0,
  },
};

// ── Token interpolation ──────────────────────────────────────────────────────

function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

function lerpColor(colorA: string, colorB: string, t: number): string {
  const parseHex = (hex: string): [number, number, number] => {
    const clean = hex.replace("#", "");
    const r = parseInt(clean.slice(0, 2), 16);
    const g = parseInt(clean.slice(2, 4), 16);
    const b = parseInt(clean.slice(4, 6), 16);
    return [r, g, b];
  };

  const [r1, g1, b1] = parseHex(colorA);
  const [r2, g2, b2] = parseHex(colorB);

  const r = Math.round(lerp(r1, r2, t));
  const g = Math.round(lerp(g1, g2, t));
  const b = Math.round(lerp(b1, b2, t));

  return `#${r.toString(16).padStart(2, "0")}${g.toString(16).padStart(2, "0")}${b.toString(16).padStart(2, "0")}`;
}

function blendTokens(
  primary: PersonaTokenSet,
  secondary: PersonaTokenSet | null,
  secondaryWeight: number,
): PersonaTokenSet {
  if (!secondary || secondaryWeight === 0) return primary;

  const t = secondaryWeight / 100;

  return {
    fontDisplay: t > 0.5 ? secondary.fontDisplay : primary.fontDisplay,
    fontBody: t > 0.5 ? secondary.fontBody : primary.fontBody,
    fontWeightDisplay: Math.round(lerp(primary.fontWeightDisplay, secondary.fontWeightDisplay, t)),
    fontWeightBody: Math.round(lerp(primary.fontWeightBody, secondary.fontWeightBody, t)),
    typeScale: lerp(primary.typeScale, secondary.typeScale, t),
    colorPrimary: lerpColor(primary.colorPrimary, secondary.colorPrimary, t),
    colorSecondary: lerpColor(primary.colorSecondary, secondary.colorSecondary, t),
    colorAccent: lerpColor(primary.colorAccent, secondary.colorAccent, t),
    colorBackground: lerpColor(primary.colorBackground, secondary.colorBackground, t),
    colorSurface: lerpColor(primary.colorSurface, secondary.colorSurface, t),
    colorTextPrimary: lerpColor(primary.colorTextPrimary, secondary.colorTextPrimary, t),
    colorTextSecondary: lerpColor(primary.colorTextSecondary, secondary.colorTextSecondary, t),
    colorBorder: lerpColor(primary.colorBorder, secondary.colorBorder, t),
    spacingBase: lerp(primary.spacingBase, secondary.spacingBase, t),
    gapSm: lerp(primary.gapSm, secondary.gapSm, t),
    gapMd: lerp(primary.gapMd, secondary.gapMd, t),
    gapLg: lerp(primary.gapLg, secondary.gapLg, t),
    radiusSm: Math.round(lerp(primary.radiusSm, secondary.radiusSm, t)),
    radiusMd: Math.round(lerp(primary.radiusMd, secondary.radiusMd, t)),
    radiusLg: Math.round(lerp(primary.radiusLg, secondary.radiusLg, t)),
    radiusFull: Math.round(lerp(primary.radiusFull, secondary.radiusFull, t)),
    shadowSm: t > 0.5 ? secondary.shadowSm : primary.shadowSm,
    shadowMd: t > 0.5 ? secondary.shadowMd : primary.shadowMd,
    shadowLg: t > 0.5 ? secondary.shadowLg : primary.shadowLg,
    motionSpeedFast: Math.round(lerp(primary.motionSpeedFast, secondary.motionSpeedFast, t)),
    motionSpeedMed: Math.round(lerp(primary.motionSpeedMed, secondary.motionSpeedMed, t)),
    motionSpeedSlow: Math.round(lerp(primary.motionSpeedSlow, secondary.motionSpeedSlow, t)),
    motionEasing: t > 0.5 ? secondary.motionEasing : primary.motionEasing,
    layoutColumns: Math.round(lerp(primary.layoutColumns, secondary.layoutColumns, t)),
    layoutOffset: t > 0.5 ? secondary.layoutOffset : primary.layoutOffset,
    sectionPaddingY: lerp(primary.sectionPaddingY, secondary.sectionPaddingY, t),
  };
}

// ── Layout directive application ─────────────────────────────────────────────

function applyLayoutDirectives(
  tokens: PersonaTokenSet,
  layout: LayoutDirectives,
): PersonaTokenSet {
  const densityScale = layout.density / 5; // 0.2-2.0, normalized around 1.0 at density=5
  const whitespaceScale = layout.whitespace_ratio / 5; // same

  return {
    ...tokens,
    gapSm: tokens.gapSm * (1 / densityScale) * whitespaceScale,
    gapMd: tokens.gapMd * (1 / densityScale) * whitespaceScale,
    gapLg: tokens.gapLg * (1 / densityScale) * whitespaceScale,
    sectionPaddingY: tokens.sectionPaddingY * whitespaceScale,
    layoutColumns: Math.min(
      12,
      Math.max(1, Math.round(tokens.layoutColumns * densityScale)),
    ),
    layoutOffset:
      layout.asymmetry > 5
        ? `${((layout.asymmetry - 5) / 5) * 8}vw`
        : "0",
  };
}

// ── Schema palette override ──────────────────────────────────────────────────

function applyColorPalette(
  tokens: PersonaTokenSet,
  palette: ColorPalette,
): PersonaTokenSet {
  return {
    ...tokens,
    colorPrimary: palette.primary,
    colorSecondary: palette.secondary,
    colorAccent: palette.accent,
    colorBackground: palette.background,
    colorSurface: palette.surface,
    colorTextPrimary: palette.text_primary,
    colorTextSecondary: palette.text_secondary,
    colorBorder: palette.border,
  };
}

function applyTypography(
  tokens: PersonaTokenSet,
  typography: TypographyConfig,
): PersonaTokenSet {
  return {
    ...tokens,
    fontDisplay: `"${typography.display_font}", ${tokens.fontDisplay}`,
    fontBody: `"${typography.body_font}", ${tokens.fontBody}`,
    fontWeightDisplay: typography.weight_display,
    fontWeightBody: typography.weight_body,
    typeScale: typography.scale_ratio,
  };
}

// ── Main: schema → CSS custom properties ─────────────────────────────────────

export interface DesignTokens {
  css: string;       // The full <style> tag content
  fontUrls: string[]; // Google Fonts URLs to preload
}

export function buildDesignTokens(schema: PersonalitySchema): DesignTokens {
  const primaryTokens = personaTokens[schema.persona_blend.primary];
  const secondaryTokens = schema.persona_blend.secondary
    ? personaTokens[schema.persona_blend.secondary]
    : null;

  let tokens = blendTokens(
    primaryTokens,
    secondaryTokens,
    schema.persona_blend.secondary_weight,
  );

  tokens = applyLayoutDirectives(tokens, schema.layout_directives);
  tokens = applyColorPalette(tokens, schema.color_palette);
  tokens = applyTypography(tokens, schema.typography);

  // Build the type scale steps
  const s = tokens.typeScale;
  const baseFontSize = 1; // rem
  const step = (n: number) => (baseFontSize * Math.pow(s, n)).toFixed(4);

  const css = `:root {
  /* Typography */
  --font-display: ${tokens.fontDisplay};
  --font-body: ${tokens.fontBody};
  --font-weight-display: ${tokens.fontWeightDisplay};
  --font-weight-body: ${tokens.fontWeightBody};
  --type-scale-ratio: ${tokens.typeScale};
  --text-xs: ${step(-1)}rem;
  --text-sm: ${step(0)}rem;
  --text-base: ${step(0)}rem;
  --text-lg: ${step(1)}rem;
  --text-xl: ${step(2)}rem;
  --text-2xl: ${step(3)}rem;
  --text-3xl: ${step(4)}rem;
  --text-4xl: ${step(5)}rem;
  --text-5xl: ${step(6)}rem;

  /* Colors */
  --color-primary: ${tokens.colorPrimary};
  --color-secondary: ${tokens.colorSecondary};
  --color-accent: ${tokens.colorAccent};
  --color-background: ${tokens.colorBackground};
  --color-surface: ${tokens.colorSurface};
  --color-text-primary: ${tokens.colorTextPrimary};
  --color-text-secondary: ${tokens.colorTextSecondary};
  --color-border: ${tokens.colorBorder};

  /* Spacing */
  --spacing-base: ${tokens.spacingBase}rem;
  --gap-sm: ${tokens.gapSm.toFixed(3)}rem;
  --gap-md: ${tokens.gapMd.toFixed(3)}rem;
  --gap-lg: ${tokens.gapLg.toFixed(3)}rem;

  /* Border Radius */
  --radius-sm: ${tokens.radiusSm}px;
  --radius-md: ${tokens.radiusMd}px;
  --radius-lg: ${tokens.radiusLg}px;
  --radius-full: ${tokens.radiusFull === 9999 ? "9999px" : `${tokens.radiusFull}px`};

  /* Shadows */
  --shadow-sm: ${tokens.shadowSm};
  --shadow-md: ${tokens.shadowMd};
  --shadow-lg: ${tokens.shadowLg};

  /* Motion */
  --motion-fast: ${tokens.motionSpeedFast}ms;
  --motion-med: ${tokens.motionSpeedMed}ms;
  --motion-slow: ${tokens.motionSpeedSlow}ms;
  --motion-easing: ${tokens.motionEasing};

  /* Layout */
  --layout-columns: ${tokens.layoutColumns};
  --layout-offset: ${tokens.layoutOffset};
  --section-padding-y: ${tokens.sectionPaddingY.toFixed(3)}rem;

  /* Derived */
  --flow-direction: ${schema.layout_directives.flow_direction};
}`;

  // Determine Google Fonts to load
  const fontNames = [
    schema.typography.display_font,
    schema.typography.body_font,
  ].filter(Boolean);

  const googleFonts = ["Playfair Display", "EB Garamond", "Bebas Neue", "Nunito", "Lato", "DM Sans", "Work Sans", "Oswald", "Inter"];
  const fontsToLoad = fontNames.filter((f) =>
    googleFonts.some((g) => f.toLowerCase().includes(g.toLowerCase())),
  );

  const fontUrls = fontsToLoad.map((font) => {
    const name = font.replace(/\s+/g, "+");
    return `https://fonts.googleapis.com/css2?family=${name}:wght@300;400;500;600;700;800;900&display=swap`;
  });

  return { css, fontUrls: [...new Set(fontUrls)] };
}

/**
 * Build a mock/fallback schema for the landing page or when no schema is found.
 */
export function buildFallbackTokens(): string {
  const tokens = personaTokens["structured-professional"];
  return `:root {
  --font-display: ${tokens.fontDisplay};
  --font-body: ${tokens.fontBody};
  --color-primary: ${tokens.colorPrimary};
  --color-accent: ${tokens.colorAccent};
  --color-background: ${tokens.colorBackground};
  --color-surface: ${tokens.colorSurface};
  --color-text-primary: ${tokens.colorTextPrimary};
  --color-text-secondary: ${tokens.colorTextSecondary};
  --color-border: ${tokens.colorBorder};
  --radius-sm: ${tokens.radiusSm}px;
  --radius-md: ${tokens.radiusMd}px;
  --radius-lg: ${tokens.radiusLg}px;
  --shadow-sm: ${tokens.shadowSm};
  --shadow-md: ${tokens.shadowMd};
  --motion-fast: ${tokens.motionSpeedFast}ms;
  --motion-med: ${tokens.motionSpeedMed}ms;
  --motion-easing: ${tokens.motionEasing};
  --gap-sm: ${tokens.gapSm}rem;
  --gap-md: ${tokens.gapMd}rem;
  --gap-lg: ${tokens.gapLg}rem;
  --section-padding-y: ${tokens.sectionPaddingY}rem;
}`;
}

export { personaTokens };
