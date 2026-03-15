"use client";

/**
 * SectionWrapper — wraps each page section with persona-appropriate
 * padding, animation, and layout offset.
 */

import { motion } from "framer-motion";

interface SectionWrapperProps {
  children: React.ReactNode;
  className?: string;
  id?: string;
  /** If true, shifts section right by --layout-offset */
  applyOffset?: boolean;
  maxWidth?: string;
}

export function SectionWrapper({
  children,
  className = "",
  id,
  applyOffset = false,
  maxWidth = "72rem",
}: SectionWrapperProps) {
  return (
    <motion.section
      id={id}
      className={`section-padding ${className}`}
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{
        duration: 0.6,
        ease: [0.4, 0, 0.2, 1],
      }}
      style={{
        paddingLeft: "max(1.5rem, env(safe-area-inset-left))",
        paddingRight: "max(1.5rem, env(safe-area-inset-right))",
      }}
    >
      <div
        style={{
          maxWidth,
          marginLeft: applyOffset ? "var(--layout-offset, 0)" : "auto",
          marginRight: applyOffset ? "0" : "auto",
          width: "100%",
        }}
      >
        {children}
      </div>
    </motion.section>
  );
}
