"use client";

/**
 * PersonaCard — generic card container that adapts to the active persona's
 * card variant (flat, raised, bordered, ghost).
 */

import { motion } from "framer-motion";

interface PersonaCardProps {
  children: React.ReactNode;
  className?: string;
  variant?: "flat" | "raised" | "bordered" | "ghost";
  onClick?: () => void;
  hoverable?: boolean;
  style?: React.CSSProperties;
}

export function PersonaCard({
  children,
  className = "",
  variant = "bordered",
  onClick,
  hoverable = false,
  style,
}: PersonaCardProps) {
  const baseStyles: React.CSSProperties = {
    borderRadius: "var(--radius-lg)",
    padding: "var(--gap-md)",
    fontFamily: "var(--font-body)",
    transition: "all var(--motion-fast) var(--motion-easing)",
    cursor: onClick ? "pointer" : undefined,
    ...style,
  };

  const variantStyles: Record<string, React.CSSProperties> = {
    flat: {
      background: "transparent",
      border: "none",
      boxShadow: "none",
    },
    raised: {
      background: "var(--color-surface)",
      border: "none",
      boxShadow: "var(--shadow-md)",
    },
    bordered: {
      background: "var(--color-surface)",
      border: "1px solid var(--color-border)",
      boxShadow: "var(--shadow-sm)",
    },
    ghost: {
      background: "var(--color-background)",
      border: "1px solid var(--color-border)",
      boxShadow: "none",
    },
  };

  return (
    <motion.div
      className={className}
      style={{ ...baseStyles, ...variantStyles[variant] }}
      onClick={onClick}
      whileHover={
        hoverable
          ? {
              scale: 1.02,
              boxShadow: "var(--shadow-lg)",
            }
          : undefined
      }
    >
      {children}
    </motion.div>
  );
}
