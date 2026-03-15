"use client";

/**
 * DatingHero — Hero section for Dating mode.
 * Shows avatar, name, and personality tagline.
 */

import { motion } from "framer-motion";
import Image from "next/image";
import type { PersonalitySchema } from "@/types/personality-schema";
import { getLayoutMode } from "@/lib/persona-engine";

interface DatingHeroProps {
  schema: PersonalitySchema;
}

export function DatingHero({ schema }: DatingHeroProps) {
  const layout = getLayoutMode(schema);
  const isLeftAligned = layout.heroVariant === "left-aligned";

  const container = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.1, delayChildren: 0.15 },
    },
  };

  const item = {
    hidden: { opacity: 0, y: 28 },
    show: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.65, ease: [0.4, 0, 0.2, 1] as [number, number, number, number] },
    },
  };

  return (
    <header
      style={{
        minHeight: "70vh",
        display: "flex",
        alignItems: "center",
        justifyContent: isLeftAligned ? "flex-start" : "center",
        paddingTop: "var(--section-padding-y)",
        paddingBottom: "var(--section-padding-y)",
        paddingLeft: "max(1.5rem, env(safe-area-inset-left))",
        paddingRight: "max(1.5rem, env(safe-area-inset-right))",
        background: "var(--color-background)",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Background gradient accent */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: `radial-gradient(ellipse at ${isLeftAligned ? "30%" : "50%"} 50%, var(--color-accent) 0%, transparent 65%)`,
          opacity: 0.06,
          pointerEvents: "none",
        }}
      />

      <motion.div
        style={{
          maxWidth: "64rem",
          width: "100%",
          marginLeft: isLeftAligned ? "var(--layout-offset, 0)" : "auto",
          marginRight: "auto",
          textAlign: isLeftAligned ? "left" : "center",
          display: "flex",
          flexDirection: "column",
          gap: "var(--gap-md)",
          position: "relative",
          zIndex: 1,
        }}
        variants={container}
        initial="hidden"
        animate="show"
      >
        {/* Avatar — larger for dating */}
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
                width: "10rem",
                height: "10rem",
                borderRadius: "var(--radius-full)",
                overflow: "hidden",
                border: "4px solid var(--color-accent)",
                boxShadow: "var(--shadow-lg)",
                position: "relative",
              }}
            >
              <Image
                src={schema.avatar_url}
                alt={schema.full_name}
                fill
                style={{ objectFit: "cover" }}
                priority
                sizes="10rem"
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
            color: "var(--color-text-primary)",
            margin: 0,
          }}
        >
          {schema.full_name}
        </motion.h1>

        {/* Personality tagline */}
        <motion.p
          variants={item}
          style={{
            fontFamily: "var(--font-body)",
            fontSize: "clamp(1rem, 2.5vw, var(--text-xl, 1.5rem))",
            color: "var(--color-accent)",
            fontWeight: 600,
            fontStyle: "italic",
            margin: 0,
          }}
        >
          &ldquo;{schema.dating_content.personality_tagline}&rdquo;
        </motion.p>

        {/* Dating tagline */}
        <motion.p
          variants={item}
          style={{
            fontFamily: "var(--font-body)",
            fontSize: "clamp(0.9rem, 1.8vw, var(--text-lg, 1.125rem))",
            color: "var(--color-text-secondary)",
            lineHeight: 1.7,
            maxWidth: isLeftAligned ? "42rem" : "36rem",
            marginLeft: isLeftAligned ? 0 : "auto",
            marginRight: isLeftAligned ? 0 : "auto",
            margin: 0,
          }}
        >
          {schema.dating_content.tagline}
        </motion.p>

        {/* Intro */}
        <motion.p
          variants={item}
          style={{
            fontFamily: "var(--font-body)",
            fontSize: "var(--text-base, 1rem)",
            color: "var(--color-text-secondary)",
            lineHeight: 1.75,
            maxWidth: isLeftAligned ? "44rem" : "38rem",
            marginLeft: isLeftAligned ? 0 : "auto",
            marginRight: isLeftAligned ? 0 : "auto",
            margin: 0,
          }}
        >
          {schema.dating_content.intro}
        </motion.p>

        {/* Interests */}
        {schema.dating_content.interests.length > 0 && (
          <motion.div
            variants={item}
            style={{
              display: "flex",
              flexWrap: "wrap",
              gap: "0.5rem",
              justifyContent: isLeftAligned ? "flex-start" : "center",
            }}
          >
            {schema.dating_content.interests.map((interest) => (
              <span
                key={interest}
                style={{
                  padding: "0.3rem 0.875rem",
                  background: "var(--color-surface)",
                  border: "1px solid var(--color-border)",
                  borderRadius: "var(--radius-full)",
                  fontFamily: "var(--font-body)",
                  fontSize: "0.85rem",
                  color: "var(--color-text-primary)",
                  fontWeight: 500,
                }}
              >
                {interest}
              </span>
            ))}
          </motion.div>
        )}
      </motion.div>
    </header>
  );
}
