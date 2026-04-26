'use client'

import { memo, useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Bell, CheckCircle } from '@phosphor-icons/react'

type Slot = {
  id: string
  time: string
  who: string
  state: 'live' | 'queued' | 'idle'
}

const SLOTS: Slot[] = [
  { id: 's1', time: '09:14', who: 'Mariama Diallo-Ferreira', state: 'live' },
  { id: 's2', time: '11:02', who: 'Ezra Whitfield', state: 'queued' },
  { id: 's3', time: '14:38', who: 'Yuki Tanaka-Holm', state: 'idle' },
  { id: 's4', time: '17:21', who: 'Söhnke Brüggemann', state: 'idle' },
]

const STATE_DOT: Record<Slot['state'], string> = {
  live: 'bg-emerald-500',
  queued: 'bg-amber-500',
  idle: 'bg-slate-300',
}

function BentoLiveStatusBase() {
  const [showNotif, setShowNotif] = useState(false)

  useEffect(() => {
    const tick = () => {
      setShowNotif(true)
      setTimeout(() => setShowNotif(false), 3000)
    }
    const t = setTimeout(tick, 1200)
    const interval = setInterval(tick, 6800)
    return () => {
      clearTimeout(t)
      clearInterval(interval)
    }
  }, [])

  return (
    <article className="relative h-full overflow-hidden rounded-[2.5rem] border border-slate-200/60 bg-white p-8 shadow-[0_20px_40px_-15px_rgba(15,23,42,0.05)]">
      <header className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-2 text-[11px] uppercase tracking-[0.18em] text-slate-500">
          <Bell size={12} weight="fill" className="text-slate-700" />
          Heute · 26. Apr
        </div>
        <span className="font-mono text-[10px] tabular-nums text-slate-400">
          UTC+02
        </span>
      </header>

      <ul className="flex flex-col divide-y divide-slate-100">
        {SLOTS.map((slot) => (
          <li
            key={slot.id}
            className="flex items-center gap-4 py-3 first:pt-0 last:pb-0"
          >
            <span className="font-mono text-[11px] tabular-nums text-slate-500">
              {slot.time}
            </span>
            <div className="relative">
              <span
                className={`block size-2 rounded-full ${STATE_DOT[slot.state]}`}
              />
              {slot.state === 'live' && (
                <motion.span
                  className="absolute inset-0 rounded-full bg-emerald-500/40"
                  animate={{ scale: [1, 2.4, 1], opacity: [0.6, 0, 0.6] }}
                  transition={{ duration: 1.8, repeat: Infinity, ease: 'easeOut' }}
                />
              )}
            </div>
            <span className="truncate text-[13px] text-slate-800">{slot.who}</span>
          </li>
        ))}
      </ul>

      <AnimatePresence>
        {showNotif && (
          <motion.div
            key="notif"
            initial={{ opacity: 0, y: 16, scale: 0.92 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 12, scale: 0.96 }}
            transition={{ type: 'spring', stiffness: 320, damping: 18 }}
            className="absolute bottom-6 left-6 right-6 flex items-center gap-3 rounded-2xl border border-emerald-200/70 bg-emerald-50/90 px-4 py-3 shadow-[0_8px_24px_-12px_rgba(16,185,129,0.4)] backdrop-blur"
          >
            <CheckCircle size={18} weight="fill" className="shrink-0 text-emerald-600" />
            <div className="min-w-0">
              <p className="truncate text-[12.5px] font-medium text-emerald-900">
                Mariama hat die Voice-Probe bestätigt
              </p>
              <p className="truncate text-[11px] text-emerald-700/80">
                Tonalität · 47.2% wärmer als Baseline
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </article>
  )
}

export const BentoLiveStatus = memo(BentoLiveStatusBase)
