"use client";

/**
 * CalendarWidget — Calendly embed placeholder.
 * Renders the correct iframe structure for Calendly integration.
 */

import { SectionWrapper } from "@/components/shared/SectionWrapper";

interface CalendarWidgetProps {
  calendlyUrl: string;
}

export function CalendarWidget({ calendlyUrl }: CalendarWidgetProps) {
  return (
    <SectionWrapper id="calendar">
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
            Schedule
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
            Book a conversation
          </h2>
        </div>

        {/* Calendly iframe */}
        <div
          style={{
            borderRadius: "var(--radius-lg)",
            overflow: "hidden",
            border: "1px solid var(--color-border)",
            boxShadow: "var(--shadow-md)",
            background: "var(--color-surface)",
          }}
        >
          <iframe
            src={`${calendlyUrl}?embed_domain=character.website&embed_type=Inline&hide_gdpr_banner=1`}
            width="100%"
            height="700"
            frameBorder="0"
            title="Schedule a meeting"
            loading="lazy"
            style={{ display: "block", border: "none" }}
          />
        </div>
      </div>
    </SectionWrapper>
  );
}
