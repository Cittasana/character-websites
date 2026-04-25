"use client";

/**
 * AudioPlayer — persona-styled audio player with Web Audio API waveform.
 * Fetches signed URL from backend (never exposes static public links).
 */

import { useState, useRef, useCallback, useEffect } from "react";
import { WaveformVisualizer } from "./WaveformVisualizer";

interface AudioPlayerProps {
  src: string;
  label: string;
  duration?: number;
  waveformData?: number[] | null;
  onPlay?: () => void;
  onEnd?: () => void;
}

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function AudioPlayer({
  src,
  label,
  duration,
  waveformData,
  onPlay,
  onEnd,
}: AudioPlayerProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [totalDuration, setTotalDuration] = useState(duration ?? 0);
  const [error, setError] = useState<string | null>(null);
  const [analyserNode, setAnalyserNode] = useState<AnalyserNode | null>(null);

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const sourceRef = useRef<MediaElementAudioSourceNode | null>(null);

  const initAudioContext = useCallback(() => {
    if (audioCtxRef.current || !audioRef.current) return;

    const ctx = new AudioContext();
    const analyser = ctx.createAnalyser();
    analyser.fftSize = 256;
    analyser.smoothingTimeConstant = 0.8;

    const source = ctx.createMediaElementSource(audioRef.current);
    source.connect(analyser);
    analyser.connect(ctx.destination);

    audioCtxRef.current = ctx;
    analyserRef.current = analyser;
    sourceRef.current = source;
    setAnalyserNode(analyser);
  }, []);

  const togglePlay = useCallback(async () => {
    if (!audioRef.current) return;

    try {
      if (isPlaying) {
        audioRef.current.pause();
        setIsPlaying(false);
      } else {
        initAudioContext();
        if (audioCtxRef.current?.state === "suspended") {
          await audioCtxRef.current.resume();
        }
        await audioRef.current.play();
        setIsPlaying(true);
        onPlay?.();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Playback failed");
      setIsPlaying(false);
    }
  }, [isPlaying, initAudioContext, onPlay]);

  const handleTimeUpdate = useCallback(() => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime);
    }
  }, []);

  const handleLoadedMetadata = useCallback(() => {
    if (audioRef.current) {
      setTotalDuration(audioRef.current.duration);
    }
  }, []);

  const handleEnded = useCallback(() => {
    setIsPlaying(false);
    setCurrentTime(0);
    onEnd?.();
  }, [onEnd]);

  const handleSeek = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    if (!audioRef.current || totalDuration === 0) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const ratio = x / rect.width;
    audioRef.current.currentTime = ratio * totalDuration;
  }, [totalDuration]);

  const progress = totalDuration > 0 ? currentTime / totalDuration : 0;

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      audioCtxRef.current?.close();
    };
  }, []);

  return (
    <div
      style={{
        background: "var(--color-surface)",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-lg)",
        padding: "var(--gap-md)",
        display: "flex",
        flexDirection: "column",
        gap: "0.75rem",
      }}
    >
      {/* Hidden audio element */}
      <audio
        ref={audioRef}
        src={src}
        preload="metadata"
        onTimeUpdate={handleTimeUpdate}
        onLoadedMetadata={handleLoadedMetadata}
        onEnded={handleEnded}
        onError={() => setError("Failed to load audio")}
        style={{ display: "none" }}
        crossOrigin="anonymous"
      />

      {/* Label */}
      <div
        style={{
          fontFamily: "var(--font-body)",
          fontWeight: 600,
          fontSize: "var(--text-sm, 0.875rem)",
          color: "var(--color-text-primary)",
        }}
      >
        {label}
      </div>

      {/* Waveform */}
      <div
        style={{ cursor: "pointer" }}
        onClick={handleSeek}
        role="slider"
        aria-label={`Seek in ${label}`}
        aria-valuenow={currentTime}
        aria-valuemin={0}
        aria-valuemax={totalDuration}
      >
        <WaveformVisualizer
          analyserNode={analyserNode}
          isPlaying={isPlaying}
          staticData={waveformData}
        />
      </div>

      {/* Controls */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "0.75rem",
        }}
      >
        {/* Play/Pause button */}
        <button
          onClick={togglePlay}
          style={{
            width: "2.5rem",
            height: "2.5rem",
            borderRadius: "var(--radius-full)",
            background: "var(--color-accent)",
            border: "none",
            cursor: "pointer",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "#ffffff",
            fontSize: "1rem",
            flexShrink: 0,
            transition: "opacity var(--motion-fast) var(--motion-easing)",
          }}
          aria-label={isPlaying ? "Pause" : "Play"}
          onMouseEnter={(e) => { e.currentTarget.style.opacity = "0.85"; }}
          onMouseLeave={(e) => { e.currentTarget.style.opacity = "1"; }}
        >
          {isPlaying ? "❚❚" : "▶"}
        </button>

        {/* Progress bar */}
        <div
          style={{
            flex: 1,
            height: "4px",
            background: "var(--color-border)",
            borderRadius: "var(--radius-full)",
            position: "relative",
            cursor: "pointer",
          }}
          onClick={handleSeek}
          role="progressbar"
          aria-valuenow={progress * 100}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          <div
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              height: "100%",
              width: `${progress * 100}%`,
              background: "var(--color-accent)",
              borderRadius: "var(--radius-full)",
              transition: "width 0.1s linear",
            }}
          />
        </div>

        {/* Time */}
        <span
          style={{
            fontFamily: "var(--font-body)",
            fontSize: "0.75rem",
            color: "var(--color-text-secondary)",
            fontVariantNumeric: "tabular-nums",
            flexShrink: 0,
          }}
        >
          {formatTime(currentTime)} / {formatTime(totalDuration)}
        </span>
      </div>

      {error && (
        <p
          style={{
            color: "#ef4444",
            fontSize: "0.75rem",
            fontFamily: "var(--font-body)",
            margin: 0,
          }}
        >
          {error}
        </p>
      )}
    </div>
  );
}
