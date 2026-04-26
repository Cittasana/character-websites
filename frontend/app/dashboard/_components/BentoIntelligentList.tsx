'use client'

import { memo, useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ArrowUpRight, CircleNotch } from '@phosphor-icons/react'

type Item = {
  id: string
  label: string
  meta: string
  weight: number
}

const SEED: Item[] = [
  { id: 'cv-skills', label: 'Skill-Hierarchie neu bewerten', meta: 'Persona · 14 Min', weight: 92.4 },
  { id: 'voice-tone', label: 'Voice-Sample → Tonalität abgleichen', meta: 'Audio · 41 Sek', weight: 87.1 },
  { id: 'dating-bio', label: 'Dating-Bio: Hooks #2 und #5 testen', meta: 'A/B · 2 Varianten', weight: 78.9 },
  { id: 'cv-projects', label: 'Projekte 2024 chronologisch ordnen', meta: 'CV · 6 Einträge', weight: 64.2 },
  { id: 'cv-tone', label: 'Self-Talk Härte +12% reduzieren', meta: 'Tone · global', weight: 47.2 },
]

function shuffleByWeight(items: Item[]): Item[] {
  const next = items.map((item) => ({
    ...item,
    weight: Math.max(12, Math.min(99, item.weight + (Math.random() - 0.5) * 18)),
  }))
  return next.sort((a, b) => b.weight - a.weight)
}

function BentoIntelligentListBase() {
  const [items, setItems] = useState<Item[]>(SEED)

  useEffect(() => {
    const interval = setInterval(() => {
      setItems((prev) => shuffleByWeight(prev))
    }, 3200)
    return () => clearInterval(interval)
  }, [])

  return (
    <article className="group relative h-full overflow-hidden rounded-[2.5rem] border border-slate-200/60 bg-white p-8 shadow-[0_20px_40px_-15px_rgba(15,23,42,0.05)]">
      <header className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-2 text-[11px] uppercase tracking-[0.18em] text-slate-500">
          <motion.span
            className="size-1.5 rounded-full bg-emerald-500"
            animate={{ opacity: [1, 0.35, 1] }}
            transition={{ duration: 1.6, repeat: Infinity, ease: 'easeInOut' }}
          />
          Priorisierung läuft
        </div>
        <CircleNotch
          size={14}
          weight="bold"
          className="animate-[spin_4s_linear_infinite] text-slate-300"
        />
      </header>

      <ol className="flex flex-col gap-1.5">
        <AnimatePresence initial={false}>
          {items.map((item, index) => (
            <motion.li
              key={item.id}
              layout
              layoutId={item.id}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ type: 'spring', stiffness: 100, damping: 20 }}
              className="flex items-center justify-between gap-4 rounded-xl px-3 py-2.5 hover:bg-slate-50"
            >
              <div className="flex min-w-0 items-center gap-4">
                <span className="font-mono text-[11px] tabular-nums text-slate-400">
                  {String(index + 1).padStart(2, '0')}
                </span>
                <div className="min-w-0">
                  <p className="truncate text-[13.5px] font-medium text-slate-900">
                    {item.label}
                  </p>
                  <p className="truncate text-[11px] text-slate-500">{item.meta}</p>
                </div>
              </div>
              <span className="font-mono text-[11px] tabular-nums text-slate-600">
                {item.weight.toFixed(1)}
              </span>
            </motion.li>
          ))}
        </AnimatePresence>
      </ol>

      <footer className="mt-6 flex items-center justify-between border-t border-slate-100 pt-4 text-[12px] text-slate-500">
        <span>Modell · cw-rank-v3</span>
        <button className="inline-flex items-center gap-1 text-slate-900 transition active:translate-y-[1px]">
          Alle ansehen
          <ArrowUpRight size={12} weight="bold" />
        </button>
      </footer>
    </article>
  )
}

export const BentoIntelligentList = memo(BentoIntelligentListBase)
