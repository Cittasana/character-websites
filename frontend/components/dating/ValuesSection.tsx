"use client";

/**
 * ValuesSection — What they believe in & what they're looking for.
 */

import { motion } from "framer-motion";
import type { PersonalitySchema } from "@/types/personality-schema";
import { SectionWrapper } from "@/components/shared/SectionWrapper";

interface ValuesSectionProps {
  schema: PersonalitySchema;
}

export function ValuesSection({ schema }: ValuesSectionProps) {
  const { dating_content } = schema;

  if (!dating_content.values.length && !dating_content.looking_for.length) {
    return null;
  }

  return (
    <SectionWrapper id="values">
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 24rem), 1fr))",
          gap: "var(--gap-lg)",
        }}
      >
        {/* Values */}
        {dating_content.values.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            style={{ display: "flex", flexDirection: "column", gap: "var(--gap-sm)" }}
          >
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
                I believe in
              </p>
              <h2
                style={{
                  fontFamily: "var(--font-display)",
                  fontWeight: "var(--font-weight-display)" as React.CSSProperties["fontWeight"],
                  fontSize: "clamp(1.25rem, 2.5vw, var(--text-2xl, 1.75rem))",
                  color: "var(--color-text-primary)",
                  lineHeight: 1.2,
                  margin: 0,
                }}
              >
                My values
              </h2>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
              {dating_content.values.map((value, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -16 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.4, delay: i * 0.06 }}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "0.75rem",
                    padding: "0.625rem 0.875rem",
                    background: "var(--color-surface)",
                    border: "1px solid var(--color-border)",
                    borderRadius: "var(--radius-md)",
                  }}
                >
                  <span
                    style={{
                      width: "0.5rem",
                      height: "0.5rem",
                      borderRadius: "var(--radius-full)",
                      background: "var(--color-accent)",
                      flexShrink: 0,
                    }}
                  />
                  <span
                    style={{
                      fontFamily: "var(--font-body)",
                      fontSize: "var(--text-base, 1rem)",
                      color: "var(--color-text-primary)",
                    }}
                  >
                    {value}
                  </span>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Looking for */}
        {dating_content.looking_for.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.1 }}
            style={{ display: "flex", flexDirection: "column", gap: "var(--gap-sm)" }}
          >
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
                I&apos;m looking for
              </p>
              <h2
                style={{
                  fontFamily: "var(--font-display)",
                  fontWeight: "var(--font-weight-display)" as React.CSSProperties["fontWeight"],
                  fontSize: "clamp(1.25rem, 2.5vw, var(--text-2xl, 1.75rem))",
                  color: "var(--color-text-primary)",
                  lineHeight: 1.2,
                  margin: 0,
                }}
              >
                What I want
              </h2>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
              {dating_content.looking_for.map((item, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: 16 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.4, delay: i * 0.06 }}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "0.75rem",
                    padding: "0.625rem 0.875rem",
                    background: "var(--color-surface)",
                    border: "1px solid var(--color-border)",
                    borderRadius: "var(--radius-md)",
                  }}
                >
                  <span
                    style={{
                      width: "0.5rem",
                      height: "0.5rem",
                      borderRadius: "var(--radius-full)",
                      background: "var(--color-primary)",
                      flexShrink: 0,
                    }}
                  />
                  <span
                    style={{
                      fontFamily: "var(--font-body)",
                      fontSize: "var(--text-base, 1rem)",
                      color: "var(--color-text-primary)",
                    }}
                  >
                    {item}
                  </span>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </div>
    </SectionWrapper>
  );
}
