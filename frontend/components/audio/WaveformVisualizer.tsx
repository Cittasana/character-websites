"use client";

/**
 * WaveformVisualizer — real-time Web Audio API waveform using AnalyserNode.
 * Renders into a <canvas> element with persona-colored bars.
 */

import { useRef, useEffect, useCallback } from "react";

interface WaveformVisualizerProps {
  analyserNode: AnalyserNode | null;
  isPlaying: boolean;
  /** Pre-computed static waveform to display when not playing */
  staticData?: number[] | null;
  color?: string;
  height?: number;
  barWidth?: number;
  barGap?: number;
}

export function WaveformVisualizer({
  analyserNode,
  isPlaying,
  staticData,
  color = "var(--color-accent, #2563eb)",
  height = 64,
  barWidth = 3,
  barGap = 1,
}: WaveformVisualizerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animFrameRef = useRef<number | null>(null);

  const drawStatic = useCallback(
    (canvas: HTMLCanvasElement, data: number[]) => {
      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      const dpr = window.devicePixelRatio || 1;
      const w = canvas.offsetWidth;
      const h = canvas.offsetHeight;
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      ctx.scale(dpr, dpr);

      ctx.clearRect(0, 0, w, h);

      const barCount = Math.floor(w / (barWidth + barGap));
      const step = Math.max(1, Math.floor(data.length / barCount));
      const centerY = h / 2;

      ctx.fillStyle = color.startsWith("var(")
        ? getComputedStyle(canvas).getPropertyValue(
            color.slice(4, -1).trim(),
          ) || "#2563eb"
        : color;

      for (let i = 0; i < barCount; i++) {
        const idx = Math.min(i * step, data.length - 1);
        const amplitude = data[idx] ?? 0;
        const barH = Math.max(2, amplitude * centerY * 1.8);
        const x = i * (barWidth + barGap);
        ctx.fillRect(x, centerY - barH / 2, barWidth, barH);
      }
    },
    [barWidth, barGap, color],
  );

  const drawLive = useCallback(
    (canvas: HTMLCanvasElement, analyser: AnalyserNode) => {
      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      const bufferLength = analyser.frequencyBinCount;
      const dataArray = new Uint8Array(bufferLength);

      const dpr = window.devicePixelRatio || 1;
      const w = canvas.offsetWidth;
      const h = canvas.offsetHeight;
      canvas.width = w * dpr;
      canvas.height = h * dpr;
      ctx.scale(dpr, dpr);

      const barCount = Math.floor(w / (barWidth + barGap));
      const step = Math.max(1, Math.floor(bufferLength / barCount));
      const centerY = h / 2;

      const resolvedColor = color.startsWith("var(")
        ? getComputedStyle(canvas).getPropertyValue(
            color.slice(4, -1).trim(),
          ) || "#2563eb"
        : color;

      const render = () => {
        if (!isPlaying) return;
        animFrameRef.current = requestAnimationFrame(render);

        analyser.getByteTimeDomainData(dataArray);

        ctx.clearRect(0, 0, w, h);
        ctx.fillStyle = resolvedColor;

        for (let i = 0; i < barCount; i++) {
          const idx = Math.min(i * step, bufferLength - 1);
          const raw = dataArray[idx] ?? 128;
          const amplitude = Math.abs((raw - 128) / 128);
          const barH = Math.max(2, amplitude * centerY * 2.5);
          const x = i * (barWidth + barGap);
          ctx.fillRect(x, centerY - barH / 2, barWidth, barH);
        }
      };

      render();
    },
    [isPlaying, barWidth, barGap, color],
  );

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    if (animFrameRef.current) {
      cancelAnimationFrame(animFrameRef.current);
      animFrameRef.current = null;
    }

    if (isPlaying && analyserNode) {
      drawLive(canvas, analyserNode);
    } else if (staticData && staticData.length > 0) {
      drawStatic(canvas, staticData);
    } else {
      // Draw flat line
      const ctx = canvas.getContext("2d");
      if (ctx) {
        const dpr = window.devicePixelRatio || 1;
        const w = canvas.offsetWidth;
        const h = canvas.offsetHeight;
        canvas.width = w * dpr;
        canvas.height = h * dpr;
        ctx.scale(dpr, dpr);
        ctx.clearRect(0, 0, w, h);

        const resolvedColor = color.startsWith("var(")
          ? getComputedStyle(canvas).getPropertyValue(
              color.slice(4, -1).trim(),
            ) || "#2563eb"
          : color;

        ctx.fillStyle = resolvedColor;
        ctx.globalAlpha = 0.3;
        const barCount = Math.floor(w / (barWidth + barGap));
        for (let i = 0; i < barCount; i++) {
          ctx.fillRect(i * (barWidth + barGap), h / 2 - 1, barWidth, 2);
        }
        ctx.globalAlpha = 1;
      }
    }

    return () => {
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current);
      }
    };
  }, [isPlaying, analyserNode, staticData, drawLive, drawStatic, color, barWidth, barGap]);

  return (
    <canvas
      ref={canvasRef}
      className="waveform-canvas"
      style={{ height: `${height}px` }}
      aria-label="Audio waveform visualization"
    />
  );
}
