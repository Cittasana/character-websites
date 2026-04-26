'use client'

import { memo } from 'react'
import { motion } from 'framer-motion'
import {
  TrendUp,
  ChartLineUp,
  Pulse,
  Eye,
  Heart,
  Waveform,
} from '@phosphor-icons/react'
import type { Icon } from '@phosphor-icons/react'

type Metric = {
  label: string
  value: string
  delta: string
  icon: Icon
  positive: boolean
}

const METRICS: Metric[] = [
  { label: 'CV-Aufrufe · 7T', value: '1.284', delta: '+12.4%', icon: Eye, positive: true },
  { label: 'Voice-Plays', value: '847', delta: '+47.2%', icon: Waveform, positive: true },
  { label: 'Persona-Match', value: '0.913', delta: '+0.041', icon: Pulse, positive: true },
  { label: 'Dating-Likes', value: '316', delta: '−4.8%', icon: Heart, positive: false },
  { label: 'Tone-Drift', value: '2.1%', delta: '−0.6%', icon: ChartLineUp, positive: true },
  { label: 'Engagement', value: '38.7%', delta: '+1.9%', icon: TrendUp, positive: true },
]

function MetricChip({ metric }: { metric: Metric }) {
  const Icon = metric.icon
  return (
    <div className="flex w-[230px] shrink-0 flex-col gap-3 rounded-2xl border border-slate-200/70 bg-slate-50/40 px-5 py-4">
      <div className="flex items-center justify-between">
        <span className="text-[11px] uppercase tracking-[0.16em] text-slate-500">
          {metric.label}
        </span>
        <Icon size={14} weight="bold" className="text-slate-400" />
      </div>
      <div className="flex items-baseline justify-between gap-3">
        <span className="font-display text-[28px] font-medium leading-none tracking-tight tabular-nums text-slate-900">
          {metric.value}
        </span>
        <span
          className={`font-mono text-[11px] tabular-nums ${
            metric.positive ? 'text-emerald-600' : 'text-rose-600'
          }`}
        >
          {metric.delta}
        </span>
      </div>
    </div>
  )
}

function BentoDataStreamBase() {
  const loop = [...METRICS, ...METRICS]

  return (
    <article className="relative h-full overflow-hidden rounded-[2.5rem] border border-slate-200/60 bg-white p-8 shadow-[0_20px_40px_-15px_rgba(15,23,42,0.05)]">
      <header className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-2 text-[11px] uppercase tracking-[0.18em] text-slate-500">
          <Pulse size={12} weight="fill" className="text-emerald-500" />
          Live · letzte 7 Tage
        </div>
        <span className="font-mono text-[10px] tabular-nums text-slate-400">
          26.04 — 04:14
        </span>
      </header>

      <div className="relative -mx-8 overflow-hidden">
        <motion.div
          className="flex gap-3 px-8"
          animate={{ x: ['0%', '-50%'] }}
          transition={{ duration: 28, repeat: Infinity, ease: 'linear' }}
          style={{ width: 'max-content' }}
        >
          {loop.map((metric, idx) => (
            <MetricChip key={`${metric.label}-${idx}`} metric={metric} />
          ))}
        </motion.div>

        <div className="pointer-events-none absolute inset-y-0 left-0 w-16 bg-gradient-to-r from-white to-transparent" />
        <div className="pointer-events-none absolute inset-y-0 right-0 w-16 bg-gradient-to-l from-white to-transparent" />
      </div>

      <footer className="mt-6 flex items-center justify-between text-[12px] text-slate-500">
        <span>Quelle · Edge-Telemetry</span>
        <span className="font-mono text-[11px] tabular-nums">+1 (312) 847-1928</span>
      </footer>
    </article>
  )
}

export const BentoDataStream = memo(BentoDataStreamBase)
