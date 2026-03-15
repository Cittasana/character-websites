"use client";

/**
 * CVHero — Hero section for CV mode.
 * Renders name, headline, and personality-driven positioning statement.
 * Layout variant (centered/left-aligned) is driven by persona.
 */

import { motion } from "framer-motion";
import Image from "next/image";
import type { PersonalitySchema } from "@/types/personality-schema";
import { getLayoutMode } from "@/lib/persona-engine";

interface CVHeroProps {
  schema: PersonalitySchema;
}

export function CVHero({ schema }: CVHeroProps) {
  const layout = getLayoutMode(schema);
  const isLeftAligned = layout.heroVariant === "left-aligned";
  const isFullBleed = layout.heroVariant === "full-bleed";

  const containerStyle: React.CSSProperties = {
    minHeight: "60vh",
    display: "flex",
    alignItems: "center",
    justifyContent: isLeftAligned ? "flex-start" : "center",
    paddingTop: "var(--section-padding-y)",
    paddingBottom: "var(--section-padding-y)",
    paddingLeft: "max(1.5rem, env(safe-area-inset-left))",
    paddingRight: "max(1.5rem, env(safe-area-inset-right))",
    position: "relative",
    overflow: "hidden",
    background: isFullBleed ? "var(--color-primary)" : "var(--color-background)",
  };

  const innerStyle: React.CSSProperties = {
    maxWidth: "64rem",
    width: "100%",
    marginLeft: isLeftAligned ? "var(--layout-offset, 0)" : "auto",
    marginRight: "auto",
    textAlign: isLeftAligned ? "left" : "center",
    display: "flex",
    flexDirection: "column",
    gap: "var(--gap-md)",
  };

  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.12,
        delayChildren: 0.1,
      },
    },
  };

  const item = {
    hidden: { opacity: 0, y: 32 },
    show: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.7,
        ease: [0.4, 0, 0.2, 1] as [number, number, number, number],
      },
    },
  };

  return (
    <header style={containerStyle}>
      <motion.div
        style={innerStyle}
        variants={container}
        initial="hidden"
        animate="show"
      >
        {/* Avatar */}
        {schema.avatar_url && (
          <motion.div
            variants={item}
            style={{
              display: "flex",
              justifyContent: isLeftAligned ? "flex-start" : "center",
            }}
          >
            <div
              style={{
                width: "7rem",
                height: "7rem",
                borderRadius: "var(--radius-full)",
                overflow: "hidden",
                border: "3px solid var(--color-accent)",
                boxShadow: "var(--shadow-lg)",
                position: "relative",
                flexShrink: 0,
              }}
            >
              <Image
                src={schema.avatar_url}
                alt={`${schema.full_name} avatar`}
                fill
                style={{ objectFit: "cover" }}
                priority
                sizes="7rem"
              />
            </div>
          </motion.div>
        )}

        {/* Name */}
        <motion.h1
          variants={item}
          style={{
            fontFamily: "var(--font-display)",
            fontWeight: "var(--font-weight-display)" as React.CSSProperties["fontWeight"],
            fontSize: "clamp(2.5rem, 6vw, var(--text-5xl, 4rem))",
            lineHeight: 1.1,
            letterSpacing: "-0.02em",
            color: isFullBleed ? "#ffffff" : "var(--color-text-primary)",
            margin: 0,
          }}
        >
          {schema.full_name}
        </motion.h1>

        {/* Headline */}
        <motion.p
          variants={item}
          style={{
            fontFamily: "var(--font-body)",
            fontSize: "clamp(1rem, 2.5vw, var(--text-xl, 1.5rem))",
            color: isFullBleed
              ? "rgba(255,255,255,0.85)"
              : "var(--color-accent)",
            fontWeight: 500,
            margin: 0,
          }}
        >
          {schema.cv_content.headline}
        </motion.p>

        {/* Positioning statement */}
        <motion.p
          variants={item}
          style={{
            fontFamily: "var(--font-body)",
            fontSize: "clamp(0.9rem, 1.8vw, var(--text-lg, 1.125rem))",
            color: isFullBleed
              ? "rgba(255,255,255,0.75)"
              : "var(--color-text-secondary)",
            lineHeight: 1.7,
            maxWidth: isLeftAligned ? "42rem" : "36rem",
            marginLeft: isLeftAligned ? 0 : "auto",
            marginRight: isLeftAligned ? 0 : "auto",
          }}
        >
          {schema.cv_content.positioning_statement}
        </motion.p>

        {/* CTA row */}
        <motion.div
          variants={item}
          style={{
            display: "flex",
            gap: "var(--gap-sm)",
            flexWrap: "wrap",
            justifyContent: isLeftAligned ? "flex-start" : "center",
          }}
        >
          {schema.website_config.calendly_url && (
            <a
              href="#calendar"
              style={{
                padding: "0.75rem 2rem",
                background: "var(--color-accent)",
                color: "#ffffff",
                borderRadius: "var(--radius-md)",
                fontFamily: "var(--font-body)",
                fontWeight: 600,
                fontSize: "var(--text-base, 1rem)",
                transition: "opacity var(--motion-fast) var(--motion-easing)",
                display: "inline-block",
              }}
            >
              Book a call
            </a>
          )}
          <a
            href="#experience"
            style={{
              padding: "0.75rem 2rem",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius-md)",
              fontFamily: "var(--font-body)",
              fontWeight: 600,
              fontSize: "var(--text-base, 1rem)",
              color: "var(--color-text-primary)",
              transition: "all var(--motion-fast) var(--motion-easing)",
              display: "inline-block",
            }}
          >
            View experience
          </a>
        </motion.div>

        {/* Skills tags */}
        {schema.cv_content.skills.length > 0 && (
          <motion.div
            variants={item}
            style={{
              display: "flex",
              flexWrap: "wrap",
              gap: "0.5rem",
              justifyContent: isLeftAligned ? "flex-start" : "center",
            }}
          >
            {schema.cv_content.skills.slice(0, 8).map((skill) => (
              <span
                key={skill}
                style={{
                  padding: "0.25rem 0.75rem",
                  background: "var(--color-surface)",
                  border: "1px solid var(--color-border)",
                  borderRadius: "var(--radius-full)",
                  fontFamily: "var(--font-body)",
                  fontSize: "0.8rem",
                  color: "var(--color-text-secondary)",
                }}
              >
                {skill}
              </span>
            ))}
          </motion.div>
        )}
      </motion.div>
    </header>
  );
}
