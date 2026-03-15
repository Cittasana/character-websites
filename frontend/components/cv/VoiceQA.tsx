"use client";

/**
 * VoiceQA — Voice Q&A widget for CV mode.
 *
 * User types a question → POST /api/retrieve/qa → receives text answer +
 * optional synthesized audio URL → plays audio with waveform visualization.
 */

import { useState, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { sendQA } from "@/lib/api";
import { WaveformVisualizer } from "@/components/audio/WaveformVisualizer";
import type { QAResponse } from "@/types/personality-schema";
import { SectionWrapper } from "@/components/shared/SectionWrapper";

interface VoiceQAProps {
  userId: string;
  mode: "cv" | "dating";
  username: string;
}

interface QAEntry {
  question: string;
  answer: string;
  audioUrl: string | null;
}

export function VoiceQA({ userId, mode }: VoiceQAProps) {
  const [question, setQuestion] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [entries, setEntries] = useState<QAEntry[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Audio state for the currently playing response
  const [playingIndex, setPlayingIndex] = useState<number | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const sourceRef = useRef<MediaElementAudioSourceNode | null>(null);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!question.trim() || isLoading) return;

      const q = question.trim();
      setQuestion("");
      setIsLoading(true);
      setError(null);

      try {
        const response: QAResponse = await sendQA({
          user_id: userId,
          question: q,
          mode,
        });

        setEntries((prev) => [
          ...prev,
          {
            question: q,
            answer: response.answer,
            audioUrl: response.audio_url,
          },
        ]);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to get answer",
        );
      } finally {
        setIsLoading(false);
      }
    },
    [question, isLoading, userId, mode],
  );

  const playAudio = useCallback(
    async (url: string, index: number) => {
      // Stop current audio
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.src = "";
      }
      audioCtxRef.current?.close();
      audioCtxRef.current = null;
      analyserRef.current = null;
      sourceRef.current = null;
      setIsPlaying(false);

      if (playingIndex === index) {
        setPlayingIndex(null);
        return;
      }

      const audio = new Audio(url);
      audio.crossOrigin = "anonymous";
      audioRef.current = audio;

      const ctx = new AudioContext();
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 256;
      analyser.smoothingTimeConstant = 0.8;

      const source = ctx.createMediaElementSource(audio);
      source.connect(analyser);
      analyser.connect(ctx.destination);

      audioCtxRef.current = ctx;
      analyserRef.current = analyser;
      sourceRef.current = source;

      audio.onended = () => {
        setIsPlaying(false);
        setPlayingIndex(null);
      };

      setPlayingIndex(index);
      setIsPlaying(true);
      await audio.play();
    },
    [playingIndex],
  );

  return (
    <SectionWrapper id="qa">
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
            Ask Me Anything
          </p>
          <h2
            style={{
              fontFamily: "var(--font-display)",
              fontWeight: "var(--font-weight-display)" as React.CSSProperties["fontWeight"],
              fontSize: "clamp(1.5rem, 3vw, var(--text-3xl, 2rem))",
              color: "var(--color-text-primary)",
              lineHeight: 1.2,
              margin: "0 0 0.5rem 0",
            }}
          >
            Voice Q&amp;A
          </h2>
          <p
            style={{
              fontFamily: "var(--font-body)",
              fontSize: "var(--text-sm, 0.875rem)",
              color: "var(--color-text-secondary)",
              margin: 0,
            }}
          >
            Ask a question and receive a personalized audio response.
          </p>
        </div>

        {/* Input form */}
        <form onSubmit={handleSubmit} style={{ display: "flex", gap: "0.75rem" }}>
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="What would you like to know?"
            disabled={isLoading}
            style={{
              flex: 1,
              padding: "0.75rem 1rem",
              background: "var(--color-surface)",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius-md)",
              fontFamily: "var(--font-body)",
              fontSize: "var(--text-base, 1rem)",
              color: "var(--color-text-primary)",
              outline: "none",
              transition: "border-color var(--motion-fast) var(--motion-easing)",
            }}
            onFocus={(e) => {
              e.currentTarget.style.borderColor = "var(--color-accent)";
            }}
            onBlur={(e) => {
              e.currentTarget.style.borderColor = "var(--color-border)";
            }}
          />
          <button
            type="submit"
            disabled={isLoading || !question.trim()}
            style={{
              padding: "0.75rem 1.5rem",
              background: "var(--color-accent)",
              color: "#ffffff",
              border: "none",
              borderRadius: "var(--radius-md)",
              fontFamily: "var(--font-body)",
              fontWeight: 600,
              fontSize: "var(--text-base, 1rem)",
              cursor: isLoading || !question.trim() ? "not-allowed" : "pointer",
              opacity: isLoading || !question.trim() ? 0.6 : 1,
              transition: "opacity var(--motion-fast) var(--motion-easing)",
              flexShrink: 0,
            }}
          >
            {isLoading ? "..." : "Ask"}
          </button>
        </form>

        {error && (
          <p
            style={{
              color: "#ef4444",
              fontFamily: "var(--font-body)",
              fontSize: "var(--text-sm, 0.875rem)",
              margin: 0,
            }}
          >
            {error}
          </p>
        )}

        {/* QA entries */}
        <AnimatePresence>
          {entries.map((entry, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.4 }}
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "0.75rem",
                padding: "var(--gap-md)",
                background: "var(--color-surface)",
                border: "1px solid var(--color-border)",
                borderRadius: "var(--radius-lg)",
                boxShadow: "var(--shadow-sm)",
              }}
            >
              {/* Question */}
              <div
                style={{
                  display: "flex",
                  gap: "0.5rem",
                  alignItems: "flex-start",
                }}
              >
                <span
                  style={{
                    width: "1.5rem",
                    height: "1.5rem",
                    borderRadius: "var(--radius-full)",
                    background: "var(--color-accent)",
                    color: "#ffffff",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: "0.7rem",
                    fontWeight: 700,
                    flexShrink: 0,
                    marginTop: "0.1rem",
                  }}
                >
                  Q
                </span>
                <p
                  style={{
                    fontFamily: "var(--font-body)",
                    fontWeight: 600,
                    fontSize: "var(--text-base, 1rem)",
                    color: "var(--color-text-primary)",
                    margin: 0,
                  }}
                >
                  {entry.question}
                </p>
              </div>

              {/* Answer */}
              <div
                style={{
                  display: "flex",
                  gap: "0.5rem",
                  alignItems: "flex-start",
                  paddingLeft: "0.5rem",
                }}
              >
                <span
                  style={{
                    width: "1.5rem",
                    height: "1.5rem",
                    borderRadius: "var(--radius-full)",
                    background: "var(--color-border)",
                    color: "var(--color-text-primary)",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: "0.7rem",
                    fontWeight: 700,
                    flexShrink: 0,
                    marginTop: "0.1rem",
                  }}
                >
                  A
                </span>
                <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                  <p
                    style={{
                      fontFamily: "var(--font-body)",
                      fontSize: "var(--text-base, 1rem)",
                      color: "var(--color-text-secondary)",
                      lineHeight: 1.65,
                      margin: 0,
                    }}
                  >
                    {entry.answer}
                  </p>

                  {/* Audio response */}
                  {entry.audioUrl && (
                    <div>
                      <WaveformVisualizer
                        analyserNode={
                          playingIndex === i ? analyserRef.current : null
                        }
                        isPlaying={playingIndex === i && isPlaying}
                        height={48}
                      />
                      <button
                        onClick={() =>
                          playAudio(entry.audioUrl!, i)
                        }
                        style={{
                          marginTop: "0.5rem",
                          display: "inline-flex",
                          alignItems: "center",
                          gap: "0.375rem",
                          padding: "0.4rem 0.875rem",
                          background:
                            playingIndex === i
                              ? "var(--color-primary)"
                              : "var(--color-background)",
                          border: "1px solid var(--color-border)",
                          borderRadius: "var(--radius-full)",
                          fontFamily: "var(--font-body)",
                          fontSize: "0.8rem",
                          fontWeight: 600,
                          color:
                            playingIndex === i
                              ? "#ffffff"
                              : "var(--color-text-primary)",
                          cursor: "pointer",
                          transition:
                            "all var(--motion-fast) var(--motion-easing)",
                        }}
                      >
                        {playingIndex === i && isPlaying ? "❚❚ Stop" : "▶ Play response"}
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {isLoading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            style={{
              padding: "var(--gap-md)",
              background: "var(--color-surface)",
              border: "1px solid var(--color-border)",
              borderRadius: "var(--radius-lg)",
              display: "flex",
              alignItems: "center",
              gap: "0.75rem",
            }}
          >
            <div
              style={{
                width: "1.25rem",
                height: "1.25rem",
                borderRadius: "var(--radius-full)",
                border: "2px solid var(--color-border)",
                borderTopColor: "var(--color-accent)",
                animation: "spin 0.8s linear infinite",
              }}
            />
            <span
              style={{
                fontFamily: "var(--font-body)",
                fontSize: "var(--text-sm, 0.875rem)",
                color: "var(--color-text-secondary)",
              }}
            >
              Generating response...
            </span>
          </motion.div>
        )}
      </div>

      <style>{`
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </SectionWrapper>
  );
}
