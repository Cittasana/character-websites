"use client";

/**
 * DimensionBar — animated progress bar for personality dimensions.
 * Fully styled by CSS custom properties.
 */

import { motion } from "framer-motion";

interface DimensionBarProps {
  label: string;
  value: number;          // 0-10
  lowLabel?: string;
  highLabel?: string;
  showLabels?: boolean;
  delay?: number;
}

export function DimensionBar({
  label,
  value,
  lowLabel,
  highLabel,
  showLabels = true,
  delay = 0,
}: DimensionBarProps) {
  const percent = (value / 10) * 100;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.375rem" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <span
          style={{
            fontFamily: "var(--font-body)",
            fontWeight: 600,
            fontSize: "var(--text-sm, 0.875rem)",
            color: "var(--color-text-primary)",
          }}
        >
          {label}
        </span>
        <span
          style={{
            fontFamily: "var(--font-body)",
            fontSize: "var(--text-sm, 0.875rem)",
            color: "var(--color-text-secondary)",
            fontVariantNumeric: "tabular-nums",
          }}
        >
          {value.toFixed(1)}
        </span>
      </div>

      {/* Track */}
      <div
        style={{
          width: "100%",
          height: "6px",
          background: "var(--color-border)",
          borderRadius: "var(--radius-full)",
          overflow: "hidden",
        }}
        role="progressbar"
        aria-valuenow={value}
        aria-valuemin={0}
        aria-valuemax={10}
        aria-label={label}
      >
        <motion.div
          initial={{ width: 0 }}
          whileInView={{ width: `${percent}%` }}
          viewport={{ once: true }}
          transition={{
            duration: 0.8,
            ease: [0.4, 0, 0.2, 1],
            delay,
          }}
          style={{
            height: "100%",
            background: "var(--color-accent)",
            borderRadius: "var(--radius-full)",
          }}
        />
      </div>

      {showLabels && (lowLabel || highLabel) && (
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            fontSize: "0.7rem",
            color: "var(--color-text-secondary)",
            fontFamily: "var(--font-body)",
          }}
        >
          <span>{lowLabel}</span>
          <span>{highLabel}</span>
        </div>
      )}
    </div>
  );
}
