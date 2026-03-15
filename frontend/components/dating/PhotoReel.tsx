"use client";

/**
 * PhotoReel — animated photo gallery with Framer Motion transitions.
 * Fetches signed photo URLs from the backend.
 */

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Image from "next/image";
import { getPhotos } from "@/lib/api";
import { SectionWrapper } from "@/components/shared/SectionWrapper";
import type { Photo } from "@/types/personality-schema";

interface PhotoReelProps {
  userId: string;
}

export function PhotoReel({ userId }: PhotoReelProps) {
  const [photos, setPhotos] = useState<Photo[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeIndex, setActiveIndex] = useState(0);
  const [direction, setDirection] = useState<1 | -1>(1);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const data = await getPhotos(userId);
        if (!cancelled) {
          const sorted = [...data].sort((a, b) => a.order - b.order);
          setPhotos(sorted);
        }
      } catch {
        // silently fail — photos are optional
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [userId]);

  const navigate = (dir: 1 | -1) => {
    setDirection(dir);
    setActiveIndex((prev) => {
      const next = prev + dir;
      if (next < 0) return photos.length - 1;
      if (next >= photos.length) return 0;
      return next;
    });
  };

  if (isLoading || photos.length === 0) return null;

  return (
    <SectionWrapper id="photos">
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
            Photos
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
            A glimpse of my world
          </h2>
        </div>

        {/* Main photo */}
        <div
          style={{
            position: "relative",
            borderRadius: "var(--radius-lg)",
            overflow: "hidden",
            aspectRatio: "4/3",
            background: "var(--color-surface)",
            maxWidth: "40rem",
            margin: "0 auto",
            width: "100%",
          }}
        >
          <AnimatePresence mode="popLayout">
            <motion.div
              key={activeIndex}
              initial={{ x: direction * 60, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: direction * -60, opacity: 0 }}
              transition={{ duration: 0.45, ease: "easeInOut" }}
              style={{ position: "absolute", inset: 0 }}
            >
              <Image
                src={photos[activeIndex].signed_url}
                alt={photos[activeIndex].alt_text ?? `Photo ${activeIndex + 1}`}
                fill
                style={{ objectFit: "cover" }}
                sizes="(max-width: 768px) 100vw, 40rem"
                priority={activeIndex === 0}
              />
            </motion.div>
          </AnimatePresence>

          {/* Navigation arrows */}
          {photos.length > 1 && (
            <>
              <button
                onClick={() => navigate(-1)}
                style={{
                  position: "absolute",
                  left: "0.75rem",
                  top: "50%",
                  transform: "translateY(-50%)",
                  width: "2.5rem",
                  height: "2.5rem",
                  borderRadius: "var(--radius-full)",
                  background: "rgba(0,0,0,0.4)",
                  border: "none",
                  color: "#ffffff",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "1rem",
                  zIndex: 2,
                  backdropFilter: "blur(4px)",
                }}
                aria-label="Previous photo"
              >
                ‹
              </button>
              <button
                onClick={() => navigate(1)}
                style={{
                  position: "absolute",
                  right: "0.75rem",
                  top: "50%",
                  transform: "translateY(-50%)",
                  width: "2.5rem",
                  height: "2.5rem",
                  borderRadius: "var(--radius-full)",
                  background: "rgba(0,0,0,0.4)",
                  border: "none",
                  color: "#ffffff",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "1rem",
                  zIndex: 2,
                  backdropFilter: "blur(4px)",
                }}
                aria-label="Next photo"
              >
                ›
              </button>
            </>
          )}

          {/* Dot indicators */}
          {photos.length > 1 && (
            <div
              style={{
                position: "absolute",
                bottom: "0.75rem",
                left: "50%",
                transform: "translateX(-50%)",
                display: "flex",
                gap: "0.375rem",
                zIndex: 2,
              }}
            >
              {photos.map((_, i) => (
                <button
                  key={i}
                  onClick={() => {
                    setDirection(i > activeIndex ? 1 : -1);
                    setActiveIndex(i);
                  }}
                  style={{
                    width: i === activeIndex ? "1.5rem" : "0.5rem",
                    height: "0.5rem",
                    borderRadius: "var(--radius-full)",
                    background:
                      i === activeIndex ? "#ffffff" : "rgba(255,255,255,0.5)",
                    border: "none",
                    cursor: "pointer",
                    padding: 0,
                    transition: "all var(--motion-fast) var(--motion-easing)",
                  }}
                  aria-label={`Go to photo ${i + 1}`}
                />
              ))}
            </div>
          )}
        </div>

        {/* Thumbnail strip */}
        {photos.length > 1 && (
          <div
            style={{
              display: "flex",
              gap: "0.5rem",
              justifyContent: "center",
              flexWrap: "wrap",
            }}
          >
            {photos.map((photo, i) => (
              <motion.button
                key={photo.id}
                onClick={() => {
                  setDirection(i > activeIndex ? 1 : -1);
                  setActiveIndex(i);
                }}
                whileHover={{ scale: 1.05 }}
                style={{
                  width: "4rem",
                  height: "4rem",
                  borderRadius: "var(--radius-sm)",
                  overflow: "hidden",
                  border: i === activeIndex
                    ? "2px solid var(--color-accent)"
                    : "2px solid transparent",
                  cursor: "pointer",
                  padding: 0,
                  position: "relative",
                  background: "var(--color-border)",
                  flexShrink: 0,
                }}
                aria-label={`View photo ${i + 1}`}
              >
                <Image
                  src={photo.signed_url}
                  alt={photo.alt_text ?? `Thumbnail ${i + 1}`}
                  fill
                  style={{ objectFit: "cover" }}
                  sizes="4rem"
                />
              </motion.button>
            ))}
          </div>
        )}
      </div>
    </SectionWrapper>
  );
}
