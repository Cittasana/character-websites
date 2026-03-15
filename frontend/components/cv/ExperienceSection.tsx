"use client";

/**
 * ExperienceSection — Experience & Achievements.
 * Renders as timeline (low density) or card grid (high density),
 * driven by layout_directives.density from the personality schema.
 */

import { motion } from "framer-motion";
import type { PersonalitySchema, WorkExperience } from "@/types/personality-schema";
import { SectionWrapper } from "@/components/shared/SectionWrapper";

interface ExperienceSectionProps {
  schema: PersonalitySchema;
}

export function ExperienceSection({ schema }: ExperienceSectionProps) {
  const { cv_content, layout_directives } = schema;
  const isTimeline = layout_directives.density <= 5;

  if (cv_content.work_history.length === 0) return null;

  return (
    <SectionWrapper id="experience" applyOffset={schema.layout_directives.asymmetry > 6}>
      <div style={{ display: "flex", flexDirection: "column", gap: "var(--gap-md)" }}>
        {/* Section header */}
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
            Career
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
            Experience & Achievements
          </h2>
        </div>

        {/* Experience entries */}
        {isTimeline ? (
          <TimelineLayout entries={cv_content.work_history} />
        ) : (
          <CardGridLayout entries={cv_content.work_history} />
        )}

        {/* Education */}
        {cv_content.education.length > 0 && (
          <div style={{ marginTop: "var(--gap-md)" }}>
            <h3
              style={{
                fontFamily: "var(--font-display)",
                fontWeight: "var(--font-weight-display)" as React.CSSProperties["fontWeight"],
                fontSize: "var(--text-xl, 1.5rem)",
                color: "var(--color-text-primary)",
                marginBottom: "var(--gap-sm)",
              }}
            >
              Education
            </h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
              {cv_content.education.map((edu, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 16 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.4, delay: i * 0.06 }}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "flex-start",
                    gap: "1rem",
                    flexWrap: "wrap",
                    padding: "0.75rem",
                    background: "var(--color-surface)",
                    borderRadius: "var(--radius-md)",
                    border: "1px solid var(--color-border)",
                  }}
                >
                  <div>
                    <p
                      style={{
                        fontFamily: "var(--font-body)",
                        fontWeight: 600,
                        fontSize: "var(--text-base, 1rem)",
                        color: "var(--color-text-primary)",
                        margin: 0,
                      }}
                    >
                      {edu.degree} in {edu.field}
                    </p>
                    <p
                      style={{
                        fontFamily: "var(--font-body)",
                        fontSize: "var(--text-sm, 0.875rem)",
                        color: "var(--color-text-secondary)",
                        margin: 0,
                      }}
                    >
                      {edu.institution}
                    </p>
                  </div>
                  {edu.year && (
                    <span
                      style={{
                        fontFamily: "var(--font-body)",
                        fontSize: "var(--text-sm, 0.875rem)",
                        color: "var(--color-text-secondary)",
                        flexShrink: 0,
                      }}
                    >
                      {edu.year}
                    </span>
                  )}
                </motion.div>
              ))}
            </div>
          </div>
        )}
      </div>
    </SectionWrapper>
  );
}

// ── Timeline layout ───────────────────────────────────────────────────────────

function TimelineLayout({ entries }: { entries: WorkExperience[] }) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 0,
        position: "relative",
      }}
    >
      {/* Vertical line */}
      <div
        style={{
          position: "absolute",
          left: "1.25rem",
          top: "1.5rem",
          bottom: "1.5rem",
          width: "2px",
          background: "var(--color-border)",
        }}
      />

      {entries.map((entry, i) => (
        <motion.div
          key={i}
          initial={{ opacity: 0, x: -24 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: i * 0.08 }}
          style={{
            display: "flex",
            gap: "1.5rem",
            paddingLeft: "0",
            paddingBottom: "var(--gap-md)",
            position: "relative",
          }}
        >
          {/* Timeline dot */}
          <div
            style={{
              width: "2.5rem",
              height: "2.5rem",
              borderRadius: "var(--radius-full)",
              background: "var(--color-surface)",
              border: "2px solid var(--color-accent)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
              zIndex: 1,
            }}
          >
            <span
              style={{
                fontFamily: "var(--font-body)",
                fontSize: "0.625rem",
                fontWeight: 700,
                color: "var(--color-accent)",
              }}
            >
              {new Date(entry.start_date).getFullYear()}
            </span>
          </div>

          {/* Content */}
          <div style={{ flex: 1, paddingTop: "0.4rem" }}>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "flex-start",
                gap: "1rem",
                flexWrap: "wrap",
                marginBottom: "0.375rem",
              }}
            >
              <div>
                <h3
                  style={{
                    fontFamily: "var(--font-display)",
                    fontWeight: "var(--font-weight-display)" as React.CSSProperties["fontWeight"],
                    fontSize: "var(--text-lg, 1.125rem)",
                    color: "var(--color-text-primary)",
                    margin: 0,
                  }}
                >
                  {entry.role}
                </h3>
                <p
                  style={{
                    fontFamily: "var(--font-body)",
                    fontSize: "var(--text-sm, 0.875rem)",
                    color: "var(--color-accent)",
                    fontWeight: 500,
                    margin: 0,
                  }}
                >
                  {entry.company}
                  {entry.location && ` · ${entry.location}`}
                </p>
              </div>
              <span
                style={{
                  fontFamily: "var(--font-body)",
                  fontSize: "0.75rem",
                  color: "var(--color-text-secondary)",
                  flexShrink: 0,
                  paddingTop: "0.25rem",
                }}
              >
                {formatDateRange(entry.start_date, entry.end_date)}
              </span>
            </div>

            <p
              style={{
                fontFamily: "var(--font-body)",
                fontSize: "var(--text-sm, 0.875rem)",
                color: "var(--color-text-secondary)",
                lineHeight: 1.65,
                marginBottom: "0.5rem",
              }}
            >
              {entry.description}
            </p>

            {entry.achievements.length > 0 && (
              <ul
                style={{
                  margin: 0,
                  paddingLeft: "1.25rem",
                  display: "flex",
                  flexDirection: "column",
                  gap: "0.25rem",
                }}
              >
                {entry.achievements.map((ach, j) => (
                  <li
                    key={j}
                    style={{
                      fontFamily: "var(--font-body)",
                      fontSize: "var(--text-sm, 0.875rem)",
                      color: "var(--color-text-secondary)",
                      lineHeight: 1.5,
                    }}
                  >
                    {ach}
                  </li>
                ))}
              </ul>
            )}
          </div>
        </motion.div>
      ))}
    </div>
  );
}

// ── Card grid layout ──────────────────────────────────────────────────────────

function CardGridLayout({ entries }: { entries: WorkExperience[] }) {
  return (
    <div
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(min(100%, 22rem), 1fr))",
        gap: "var(--gap-md)",
      }}
    >
      {entries.map((entry, i) => (
        <motion.div
          key={i}
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.4, delay: i * 0.06 }}
          style={{
            background: "var(--color-surface)",
            border: "1px solid var(--color-border)",
            borderRadius: "var(--radius-lg)",
            padding: "var(--gap-md)",
            display: "flex",
            flexDirection: "column",
            gap: "0.625rem",
            boxShadow: "var(--shadow-sm)",
          }}
        >
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "flex-start",
              gap: "0.5rem",
            }}
          >
            <div>
              <h3
                style={{
                  fontFamily: "var(--font-display)",
                  fontWeight: "var(--font-weight-display)" as React.CSSProperties["fontWeight"],
                  fontSize: "var(--text-base, 1rem)",
                  color: "var(--color-text-primary)",
                  margin: 0,
                }}
              >
                {entry.role}
              </h3>
              <p
                style={{
                  fontFamily: "var(--font-body)",
                  fontSize: "var(--text-sm, 0.875rem)",
                  color: "var(--color-accent)",
                  fontWeight: 500,
                  margin: 0,
                }}
              >
                {entry.company}
              </p>
            </div>
            <span
              style={{
                fontFamily: "var(--font-body)",
                fontSize: "0.7rem",
                color: "var(--color-text-secondary)",
                flexShrink: 0,
                background: "var(--color-background)",
                padding: "0.15rem 0.5rem",
                borderRadius: "var(--radius-full)",
                border: "1px solid var(--color-border)",
              }}
            >
              {new Date(entry.start_date).getFullYear()}
              {entry.end_date ? `–${new Date(entry.end_date).getFullYear()}` : "–now"}
            </span>
          </div>

          <p
            style={{
              fontFamily: "var(--font-body)",
              fontSize: "var(--text-sm, 0.875rem)",
              color: "var(--color-text-secondary)",
              lineHeight: 1.6,
              margin: 0,
            }}
          >
            {entry.description}
          </p>

          {entry.achievements.length > 0 && (
            <ul
              style={{
                margin: 0,
                paddingLeft: "1.25rem",
                display: "flex",
                flexDirection: "column",
                gap: "0.2rem",
              }}
            >
              {entry.achievements.slice(0, 3).map((ach, j) => (
                <li
                  key={j}
                  style={{
                    fontFamily: "var(--font-body)",
                    fontSize: "0.8rem",
                    color: "var(--color-text-secondary)",
                    lineHeight: 1.4,
                  }}
                >
                  {ach}
                </li>
              ))}
            </ul>
          )}
        </motion.div>
      ))}
    </div>
  );
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function formatDateRange(start: string, end: string | null): string {
  const startDate = new Date(start);
  const startStr = startDate.toLocaleDateString("en-US", {
    month: "short",
    year: "numeric",
  });

  if (!end) return `${startStr} – Present`;

  const endDate = new Date(end);
  const endStr = endDate.toLocaleDateString("en-US", {
    month: "short",
    year: "numeric",
  });

  return `${startStr} – ${endStr}`;
}
