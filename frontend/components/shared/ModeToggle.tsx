"use client";

/**
 * Mode Toggle — switches between CV and Dating modes.
 * Renders as a floating tab/pill using persona design tokens.
 */

import Link from "next/link";

interface ModeToggleProps {
  username: string;
  currentMode: "cv" | "dating";
}

export function ModeToggle({ username, currentMode }: ModeToggleProps) {
  return (
    <nav
      style={{
        position: "fixed",
        top: "1rem",
        right: "1rem",
        zIndex: 100,
        display: "flex",
        gap: "0.25rem",
        background: "var(--color-surface)",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-full)",
        padding: "0.25rem",
        boxShadow: "var(--shadow-md)",
      }}
      aria-label="Site mode"
    >
      <Link
        href={`/${username}/cv`}
        style={{
          padding: "0.4rem 1rem",
          borderRadius: "var(--radius-full)",
          fontSize: "0.875rem",
          fontWeight: 600,
          fontFamily: "var(--font-body)",
          transition: "all var(--motion-fast) var(--motion-easing)",
          background: currentMode === "cv" ? "var(--color-primary)" : "transparent",
          color: currentMode === "cv" ? "#ffffff" : "var(--color-text-secondary)",
          textDecoration: "none",
        }}
        aria-current={currentMode === "cv" ? "page" : undefined}
      >
        CV
      </Link>
      <Link
        href={`/${username}/dating`}
        style={{
          padding: "0.4rem 1rem",
          borderRadius: "var(--radius-full)",
          fontSize: "0.875rem",
          fontWeight: 600,
          fontFamily: "var(--font-body)",
          transition: "all var(--motion-fast) var(--motion-easing)",
          background: currentMode === "dating" ? "var(--color-primary)" : "transparent",
          color: currentMode === "dating" ? "#ffffff" : "var(--color-text-secondary)",
          textDecoration: "none",
        }}
        aria-current={currentMode === "dating" ? "page" : undefined}
      >
        Dating
      </Link>
    </nav>
  );
}
