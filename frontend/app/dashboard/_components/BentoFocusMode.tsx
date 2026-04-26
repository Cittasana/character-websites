'use client'

import { memo, useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  TextAa,
  Quotes,
  Microphone,
  PencilSimpleLine,
} from '@phosphor-icons/react'

const PARAGRAPH = [
  'Ich baue Räume,',
  'in denen Geräusche',
  'eine Form bekommen.',
  'Manchmal Beton, manchmal',
  'eine sehr leise Frage.',
]

function BentoFocusModeBase() {
  const [active, setActive] = useState(2)
  const [showToolbar, setShowToolbar] = useState(false)

  useEffect(() => {
    const interval = setInterval(() => {
      setActive((prev) => (prev + 1) % PARAGRAPH.length)
    }, 1400)
    const t = setTimeout(() => setShowToolbar(true), 900)
    return () => {
      clearInterval(interval)
      clearTimeout(t)
    }
  }, [])

  return (
    <article className="relative h-full overflow-hidden rounded-[2.5rem] border border-slate-200/60 bg-white p-8 shadow-[0_20px_40px_-15px_rgba(15,23,42,0.05)]">
      <header className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-2 text-[11px] uppercase tracking-[0.18em] text-slate-500">
          <Quotes size={12} weight="fill" className="text-slate-700" />
          Bio · Entwurf 03
        </div>
        <span className="font-mono text-[10px] tabular-nums text-slate-400">
          268 Zeichen
        </span>
      </header>

      <div className="font-display text-[22px] leading-[1.25] tracking-tight text-slate-900">
        {PARAGRAPH.map((line, idx) => (
          <motion.span
            key={`${line}-${idx}`}
            className="block"
            animate={{
              opacity: idx === active ? 1 : 0.32,
              x: idx === active ? 0 : -2,
            }}
            transition={{ type: 'spring', stiffness: 120, damping: 22 }}
          >
            {line}
          </motion.span>
        ))}
      </div>

      <AnimatePresence>
        {showToolbar && (
          <motion.div
            key="toolbar"
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            transition={{ type: 'spring', stiffness: 140, damping: 20 }}
            className="absolute bottom-6 left-6 right-6 flex items-center justify-between rounded-full border border-slate-200/70 bg-white/85 px-5 py-2.5 shadow-[0_12px_30px_-10px_rgba(15,23,42,0.18)] backdrop-blur"
          >
            <div className="flex items-center gap-1">
              <ToolbarBtn>
                <TextAa size={14} weight="bold" />
              </ToolbarBtn>
              <ToolbarBtn>
                <PencilSimpleLine size={14} weight="bold" />
              </ToolbarBtn>
              <ToolbarBtn>
                <Microphone size={14} weight="bold" />
              </ToolbarBtn>
            </div>
            <span className="font-mono text-[11px] tabular-nums text-slate-500">
              Ton · 0.74
            </span>
          </motion.div>
        )}
      </AnimatePresence>
    </article>
  )
}

function ToolbarBtn({ children }: { children: React.ReactNode }) {
  return (
    <button className="grid size-8 place-items-center rounded-full text-slate-700 transition hover:bg-slate-100 active:translate-y-[1px]">
      {children}
    </button>
  )
}

export const BentoFocusMode = memo(BentoFocusModeBase)
