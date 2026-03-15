"use client";

/**
 * VoiceClipsGallery — fetches and displays signed voice clips from the backend.
 * Each clip renders with Web Audio waveform visualization.
 * Voice files are NEVER public — always loaded via signed URLs.
 */

import { useState, useEffect } from "react";
import { getVoiceClips } from "@/lib/api";
import { AudioPlayer } from "@/components/audio/AudioPlayer";
import { SectionWrapper } from "@/components/shared/SectionWrapper";
import type { VoiceClip } from "@/types/personality-schema";

interface VoiceClipsGalleryProps {
  userId: string;
}

export function VoiceClipsGallery({ userId }: VoiceClipsGalleryProps) {
  const [clips, setClips] = useState<VoiceClip[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const response = await getVoiceClips(userId);
        if (!cancelled) {
          setClips(response.clips);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "Failed to load voice clips",
          );
        }
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [userId]);

  if (isLoading) {
    return (
      <SectionWrapper>
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "0.75rem",
          }}
        >
          <SkeletonBar />
          <SkeletonBar />
          <SkeletonBar />
        </div>
      </SectionWrapper>
    );
  }

  if (error || clips.length === 0) return null;

  return (
    <SectionWrapper id="voice-clips">
      <div style={{ display: "flex", flexDirection: "column", gap: "var(--gap-md)" }}>
        {/* Header */}
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
            Voice
          </p>
          <h2
            style={{
              fontFamily: "var(--font-display)",
              fontWeight: "var(--font-weight-display)" as React.CSSProperties["fontWeight"],
              fontSize: "clamp(1.5rem, 3vw, var(--text-3xl, 2rem))",
              color: "var(--color-text-primary)",
              lineHeight: 1.2,
              margin: "0 0 0.25rem 0",
            }}
          >
            Hear my voice
          </h2>
          <p
            style={{
              fontFamily: "var(--font-body)",
              fontSize: "var(--text-sm, 0.875rem)",
              color: "var(--color-text-secondary)",
              margin: 0,
            }}
          >
            Authentic voice clips — because a voice tells you so much.
          </p>
        </div>

        {/* Clips grid */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(min(100%, 28rem), 1fr))",
            gap: "var(--gap-sm)",
          }}
        >
          {clips.map((clip) => (
            <AudioPlayer
              key={clip.id}
              src={clip.signed_url}
              label={clip.label}
              duration={clip.duration_seconds}
              waveformData={clip.waveform_data}
            />
          ))}
        </div>
      </div>
    </SectionWrapper>
  );
}

function SkeletonBar() {
  return (
    <div
      style={{
        height: "5rem",
        borderRadius: "var(--radius-lg)",
        background: "var(--color-border)",
        animation: "pulse 1.5s ease-in-out infinite",
      }}
    />
  );
}
