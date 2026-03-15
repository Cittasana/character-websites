"use client";

/**
 * PersonalityInsights — CV mode section showing Claude-generated character
 * summary and 7-dimension visual bar chart.
 */

import { motion } from "framer-motion";
import type { PersonalitySchema } from "@/types/personality-schema";
import { getDimensionVisuals } from "@/lib/persona-engine";
import { DimensionBar } from "@/components/shared/DimensionBar";
import { SectionWrapper } from "@/components/shared/SectionWrapper";

interface PersonalityInsightsProps {
  schema: PersonalitySchema;
}

export function PersonalityInsights({ schema }: PersonalityInsightsProps) {
  if (!schema.website_config.show_personality_insights) return null;

  const dimensions = getDimensionVisuals(schema.dimensions);

  return (
    <SectionWrapper id="personality">
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 28rem), 1fr))",
          gap: "var(--gap-lg)",
          alignItems: "start",
        }}
      >
        {/* Left: summary text */}
        <motion.div
          initial={{ opacity: 0, x: -24 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, ease: [0.4, 0, 0.2, 1] }}
          style={{ display: "flex", flexDirection: "column", gap: "var(--gap-sm)" }}
        >
          <p
            style={{
              fontFamily: "var(--font-body)",
              fontSize: "0.75rem",
              fontWeight: 700,
              letterSpacing: "0.1em",
              textTransform: "uppercase",
              color: "var(--color-accent)",
              margin: 0,
            }}
          >
            Personality Insights
          </p>

          <h2
            style={{
              fontFamily: "var(--font-display)",
              fontWeight: "var(--font-weight-display)" as React.CSSProperties["fontWeight"],
              fontSize: "clamp(1.5rem, 3vw, var(--text-3xl, 2rem))",
              color: "var(--color-text-primary)",
              lineHeight: 1.2,
              margin: 0,
            }}
          >
            Character Analysis
          </h2>

          <p
            style={{
              fontFamily: "var(--font-body)",
              fontSize: "var(--text-base, 1rem)",
              lineHeight: 1.7,
              color: "var(--color-text-secondary)",
              margin: 0,
            }}
          >
            {schema.cv_content.summary}
          </p>

          {/* Persona blend indicator */}
          <div
            style={{
              marginTop: "var(--gap-sm)",
              padding: "var(--gap-sm)",
              background: "var(--color-surface)",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius-md)",
              display: "flex",
              flexDirection: "column",
              gap: "0.5rem",
            }}
          >
            <p
              style={{
                fontFamily: "var(--font-body)",
                fontSize: "0.75rem",
                fontWeight: 700,
                textTransform: "uppercase",
                letterSpacing: "0.08em",
                color: "var(--color-text-secondary)",
                margin: 0,
              }}
            >
              Persona blend
            </p>
            <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
              <PersonaTag
                name={schema.persona_blend.primary.replace(/-/g, " ")}
                weight={schema.persona_blend.primary_weight}
                isPrimary
              />
              {schema.persona_blend.secondary && (
                <PersonaTag
                  name={schema.persona_blend.secondary.replace(/-/g, " ")}
                  weight={schema.persona_blend.secondary_weight}
                  isPrimary={false}
                />
              )}
            </div>
          </div>
        </motion.div>

        {/* Right: dimension bars */}
        <motion.div
          initial={{ opacity: 0, x: 24 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, ease: [0.4, 0, 0.2, 1], delay: 0.1 }}
          style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}
        >
          {dimensions.map((dim, i) => (
            <DimensionBar
              key={dim.label}
              label={dim.label}
              value={dim.value}
              lowLabel={dim.lowLabel}
              highLabel={dim.highLabel}
              delay={i * 0.06}
            />
          ))}
        </motion.div>
      </div>
    </SectionWrapper>
  );
}

function PersonaTag({
  name,
  weight,
  isPrimary,
}: {
  name: string;
  weight: number;
  isPrimary: boolean;
}) {
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "0.375rem",
        padding: "0.25rem 0.625rem",
        background: isPrimary ? "var(--color-accent)" : "var(--color-border)",
        color: isPrimary ? "#ffffff" : "var(--color-text-primary)",
        borderRadius: "var(--radius-full)",
        fontFamily: "var(--font-body)",
        fontSize: "0.75rem",
        fontWeight: 600,
        textTransform: "capitalize",
      }}
    >
      {name}
      <span style={{ opacity: 0.75 }}>{weight}%</span>
    </span>
  );
}
