"use client";

/**
 * PersonalityScores — Dating mode personality score cards.
 * Shows warmth, humor, ambition, adventure with persona-styled visuals.
 */

import { motion } from "framer-motion";
import type { PersonalitySchema } from "@/types/personality-schema";
import { SectionWrapper } from "@/components/shared/SectionWrapper";

interface PersonalityScoresProps {
  schema: PersonalitySchema;
}

interface ScoreCard {
  label: string;
  value: number;
  emoji: string;
  description: string;
}

export function PersonalityScores({ schema }: PersonalityScoresProps) {
  const { dimensions, dating_content } = schema;

  const scores: ScoreCard[] = [
    {
      label: "Warmth",
      value: dimensions.warmth,
      emoji: "✦",
      description: dimensions.warmth >= 7 ? "Deeply caring" : dimensions.warmth >= 4 ? "Balanced" : "Analytical",
    },
    {
      label: "Humor",
      value: dimensions.humor,
      emoji: "◑",
      description: dimensions.humor >= 7 ? "Genuinely funny" : dimensions.humor >= 4 ? "Light-hearted" : "Earnest",
    },
    {
      label: "Ambition",
      value: dating_content.ambition_score,
      emoji: "◈",
      description: dating_content.ambition_score >= 7 ? "Highly driven" : dating_content.ambition_score >= 4 ? "Motivated" : "Balanced",
    },
    {
      label: "Adventure",
      value: dating_content.adventure_score,
      emoji: "◎",
      description: dating_content.adventure_score >= 7 ? "Always exploring" : dating_content.adventure_score >= 4 ? "Open to new things" : "Comfort-loving",
    },
    {
      label: "Openness",
      value: dimensions.openness,
      emoji: "◯",
      description: dimensions.openness >= 7 ? "An open book" : dimensions.openness >= 4 ? "Selectively open" : "Private",
    },
    {
      label: "Confidence",
      value: dimensions.confidence,
      emoji: "◆",
      description: dimensions.confidence >= 7 ? "Assured & bold" : dimensions.confidence >= 4 ? "Grounded" : "Humble",
    },
  ];

  return (
    <SectionWrapper id="personality-scores">
      <div style={{ display: "flex", flexDirection: "column", gap: "var(--gap-md)" }}>
        <div>
          <p
            style={{
              fontFamily: "var(--font-body)",
              fontSize: "0.75rem",
              fontWeight: 700,
              letterSpacing: "0.1em",
              textTransform: "uppercase",
              color: "var(--color-accent)",
              margin: "0 0 0.5rem 0",
            }}
          >
            Personality
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
            What I&apos;m like
          </h2>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(min(100%, 16rem), 1fr))",
            gap: "var(--gap-sm)",
          }}
        >
          {scores.map((score, i) => (
            <ScoreCardComponent key={score.label} score={score} delay={i * 0.07} />
          ))}
        </div>
      </div>
    </SectionWrapper>
  );
}

function ScoreCardComponent({ score, delay }: { score: ScoreCard; delay: number }) {
  const percent = (score.value / 10) * 100;
  const radius = 28;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (percent / 100) * circumference;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.92 }}
      whileInView={{ opacity: 1, scale: 1 }}
      viewport={{ once: true }}
      transition={{ duration: 0.45, delay, ease: [0.34, 1.56, 0.64, 1] }}
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: "0.75rem",
        padding: "var(--gap-md)",
        background: "var(--color-surface)",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-lg)",
        boxShadow: "var(--shadow-sm)",
        textAlign: "center",
      }}
    >
      {/* Circular progress */}
      <div style={{ position: "relative", width: "4.5rem", height: "4.5rem" }}>
        <svg
          width="72"
          height="72"
          viewBox="0 0 72 72"
          style={{ transform: "rotate(-90deg)" }}
        >
          {/* Track */}
          <circle
            cx="36"
            cy="36"
            r={radius}
            fill="none"
            stroke="var(--color-border)"
            strokeWidth="4"
          />
          {/* Progress */}
          <motion.circle
            cx="36"
            cy="36"
            r={radius}
            fill="none"
            stroke="var(--color-accent)"
            strokeWidth="4"
            strokeLinecap="round"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            whileInView={{ strokeDashoffset }}
            viewport={{ once: true }}
            transition={{ duration: 0.9, delay, ease: [0.4, 0, 0.2, 1] }}
          />
        </svg>

        {/* Center text */}
        <div
          style={{
            position: "absolute",
            inset: 0,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <span
            style={{
              fontSize: "1rem",
              lineHeight: 1,
            }}
          >
            {score.emoji}
          </span>
          <span
            style={{
              fontFamily: "var(--font-body)",
              fontWeight: 700,
              fontSize: "0.875rem",
              color: "var(--color-text-primary)",
              fontVariantNumeric: "tabular-nums",
            }}
          >
            {score.value.toFixed(0)}
          </span>
        </div>
      </div>

      <div>
        <p
          style={{
            fontFamily: "var(--font-body)",
            fontWeight: 700,
            fontSize: "var(--text-base, 1rem)",
            color: "var(--color-text-primary)",
            margin: 0,
          }}
        >
          {score.label}
        </p>
        <p
          style={{
            fontFamily: "var(--font-body)",
            fontSize: "var(--text-sm, 0.875rem)",
            color: "var(--color-text-secondary)",
            margin: 0,
          }}
        >
          {score.description}
        </p>
      </div>
    </motion.div>
  );
}
