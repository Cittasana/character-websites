'use client'

import { memo, useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Sparkle, MagnifyingGlass } from '@phosphor-icons/react'

const PROMPTS = [
  'Schreib eine CV-Bio im Ton von Werner Herzog',
  'Erstell drei Dating-Hooks für introvertierte Architekten',
  'Welche Projekte aus 2024 erzählen die beste Geschichte?',
  'Generiere ein Voice-Sample mit warmer Berliner Färbung',
]

const PHASE_DELAY = { type: 0.022, hold: 1800, processing: 1100 } as const

function BentoCommandInputBase() {
  const [promptIndex, setPromptIndex] = useState(0)
  const [text, setText] = useState('')
  const [phase, setPhase] = useState<'typing' | 'holding' | 'processing'>('typing')

  useEffect(() => {
    const target = PROMPTS[promptIndex]

    if (phase === 'typing') {
      if (text.length < target.length) {
        const t = setTimeout(
          () => setText(target.slice(0, text.length + 1)),
          PHASE_DELAY.type * 1000,
        )
        return () => clearTimeout(t)
      }
      const t = setTimeout(() => setPhase('holding'), PHASE_DELAY.hold)
      return () => clearTimeout(t)
    }

    if (phase === 'holding') {
      const t = setTimeout(() => setPhase('processing'), 50)
      return () => clearTimeout(t)
    }

    const t = setTimeout(() => {
      setText('')
      setPromptIndex((i) => (i + 1) % PROMPTS.length)
      setPhase('typing')
    }, PHASE_DELAY.processing)
    return () => clearTimeout(t)
  }, [text, phase, promptIndex])

  return (
    <article className="relative h-full overflow-hidden rounded-[2.5rem] border border-slate-200/60 bg-white p-8 shadow-[0_20px_40px_-15px_rgba(15,23,42,0.05)]">
      <header className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-2 text-[11px] uppercase tracking-[0.18em] text-slate-500">
          <Sparkle size={12} weight="fill" className="text-rose-500" />
          Command
        </div>
        <span className="font-mono text-[10px] tracking-wide text-slate-400">⌘ K</span>
      </header>

      <div className="flex h-[148px] flex-col justify-center">
        <p className="mb-3 text-[11px] font-medium uppercase tracking-[0.2em] text-slate-400">
          Was willst du erzählen?
        </p>

        <div className="relative flex items-center gap-3 rounded-2xl border border-slate-200 bg-slate-50/60 px-4 py-3.5">
          <MagnifyingGlass size={16} weight="bold" className="shrink-0 text-slate-400" />
          <span className="font-display text-[15px] leading-tight tracking-tight text-slate-900">
            {text}
            <motion.span
              className="ml-[1px] inline-block h-[16px] w-[2px] -translate-y-[1px] bg-slate-900 align-middle"
              animate={{ opacity: phase === 'typing' ? [1, 0, 1] : 0 }}
              transition={{ duration: 0.9, repeat: Infinity, ease: 'linear' }}
            />
          </span>

          <AnimatePresence>
            {phase === 'processing' && (
              <motion.span
                key="shimmer"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="pointer-events-none absolute inset-0 overflow-hidden rounded-2xl"
              >
                <motion.span
                  className="absolute inset-y-0 -left-1/3 w-1/3 bg-gradient-to-r from-transparent via-slate-900/[0.06] to-transparent"
                  animate={{ x: ['0%', '420%'] }}
                  transition={{ duration: 1.1, ease: 'easeInOut' }}
                />
              </motion.span>
            )}
          </AnimatePresence>
        </div>
      </div>

      <footer className="mt-6 flex items-center gap-2 text-[11px] text-slate-500">
        <span className="rounded-md bg-slate-100 px-2 py-1 font-mono text-[10px] text-slate-700">
          /persona
        </span>
        <span className="rounded-md bg-slate-100 px-2 py-1 font-mono text-[10px] text-slate-700">
          /voice
        </span>
        <span className="rounded-md bg-slate-100 px-2 py-1 font-mono text-[10px] text-slate-700">
          /cv
        </span>
        <span className="ml-auto font-mono text-[10px] tabular-nums text-slate-400">
          {String(promptIndex + 1).padStart(2, '0')} / {String(PROMPTS.length).padStart(2, '0')}
        </span>
      </footer>
    </article>
  )
}

export const BentoCommandInput = memo(BentoCommandInputBase)
