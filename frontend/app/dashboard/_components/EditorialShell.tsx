'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'
import { ArrowUpRight, CircleHalf, Sparkle } from '@phosphor-icons/react'
import { BentoIntelligentList } from './BentoIntelligentList'
import { BentoCommandInput } from './BentoCommandInput'
import { BentoLiveStatus } from './BentoLiveStatus'
import { BentoDataStream } from './BentoDataStream'
import { BentoFocusMode } from './BentoFocusMode'

type Props = {
  username: string
  needsOnboarding: boolean
}

export function EditorialShell({ username, needsOnboarding }: Props) {
  return (
    <main className="relative min-h-[100dvh] bg-[#f9fafb] text-slate-900">
      <div
        aria-hidden
        className="pointer-events-none fixed inset-0 z-50 opacity-[0.018] mix-blend-multiply"
        style={{
          backgroundImage:
            "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='180' height='180'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>\")",
        }}
      />

      <TopBar username={username} />

      <section className="mx-auto grid w-full max-w-[1400px] grid-cols-12 gap-8 px-6 pb-10 pt-16 md:px-10 md:pt-24 lg:pt-32">
        <div className="col-span-12 lg:col-span-5">
          <p className="mb-8 inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1 text-[11px] uppercase tracking-[0.16em] text-slate-600">
            <CircleHalf size={11} weight="fill" className="text-emerald-500" />
            Sitzung 4 · Persona kalibriert
          </p>
          <h1 className="font-display text-[44px] font-medium leading-[0.96] tracking-[-0.02em] text-slate-900 md:text-[72px]">
            Heute,
            <br />
            <span className="text-slate-500">26. April —</span>
            <br />
            der Ton
            <br />
            sitzt.
          </h1>
        </div>

        <div className="col-span-12 mt-2 flex flex-col justify-end gap-8 lg:col-span-6 lg:col-start-7 lg:mt-0">
          <p className="max-w-[44ch] text-[15.5px] leading-[1.65] text-slate-600">
            Willkommen zurück,{' '}
            <span className="font-medium text-slate-900">@{username}</span>. Deine
            Persona-Engine hat über Nacht 11 Mikro-Adjustierungen vorgeschlagen — Tonalität
            wärmer, Hooks präziser, ein Vorschlag zum Streichen. Drei Minuten Lesedauer.
          </p>

          {needsOnboarding ? (
            <Link
              href="/onboarding"
              className="group inline-flex w-fit items-center gap-3 rounded-full bg-slate-900 px-5 py-3 text-[13.5px] font-medium text-white transition hover:bg-slate-800 active:translate-y-[1px]"
            >
              Onboarding fertigstellen
              <span className="grid size-6 place-items-center rounded-full bg-white/12 transition group-hover:bg-white/20">
                <ArrowUpRight size={12} weight="bold" />
              </span>
            </Link>
          ) : (
            <div className="flex flex-wrap items-center gap-x-8 gap-y-4">
              <Link
                href={`/${username}/cv`}
                className="group inline-flex items-center gap-3 rounded-full bg-slate-900 px-5 py-3 text-[13.5px] font-medium text-white transition hover:bg-slate-800 active:translate-y-[1px]"
              >
                CV-Modus öffnen
                <span className="grid size-6 place-items-center rounded-full bg-white/12 transition group-hover:bg-white/20">
                  <ArrowUpRight size={12} weight="bold" />
                </span>
              </Link>
              <Link
                href="/"
                className="text-[13.5px] text-slate-600 underline-offset-4 transition hover:text-slate-900 hover:underline"
              >
                Öffentlicher Link
              </Link>
              <span className="font-mono text-[11px] tabular-nums text-slate-500">
                cw.io/{username}
              </span>
            </div>
          )}
        </div>

        <div className="col-span-12 mt-12 grid grid-cols-12 gap-6 border-t border-slate-200/80 pt-6 md:mt-16">
          <Stat label="Persona-Drift" value="0.041" delta="−12% diese Woche" />
          <Stat label="Letzte Probe" value="03:42 Uhr" delta="Heute · automatisch" />
          <Stat label="Aktive Modi" value="2 / 3" delta="CV · Voice" />
          <Stat label="Vertrauensindex" value="0.913" delta="+0.027 vs. Mo" />
        </div>
      </section>

      <section className="mx-auto w-full max-w-[1400px] px-6 pb-24 md:px-10 md:pb-32">
        <header className="mb-10 flex items-end justify-between">
          <div>
            <p className="mb-2 text-[11px] uppercase tracking-[0.2em] text-slate-500">
              Workspace
            </p>
            <h2 className="font-display text-[28px] leading-tight tracking-tight text-slate-900 md:text-[36px]">
              Was sich heute bewegt.
            </h2>
          </div>
          <span className="font-mono text-[11px] tabular-nums text-slate-500">
            04:14:02 — Berlin
          </span>
        </header>

        <div className="grid grid-cols-12 gap-6">
          <BentoCell className="col-span-12 md:col-span-4" cardHeight="h-[360px]">
            <BentoIntelligentList />
            <Caption
              eyebrow="01"
              title="Priorisierungs-Engine"
              meta="re-ranked alle 3.2 s · Modell cw-rank-v3"
            />
          </BentoCell>

          <BentoCell className="col-span-12 md:col-span-4" cardHeight="h-[360px]">
            <BentoCommandInput />
            <Caption
              eyebrow="02"
              title="Befehl in eigenen Worten"
              meta="natürliche Sprache · Slash-Befehle möglich"
            />
          </BentoCell>

          <BentoCell className="col-span-12 md:col-span-4" cardHeight="h-[360px]">
            <BentoLiveStatus />
            <Caption
              eyebrow="03"
              title="Heute im Studio"
              meta="vier Sessions · eine läuft gerade"
            />
          </BentoCell>

          <BentoCell className="col-span-12 lg:col-span-8" cardHeight="h-[300px]">
            <BentoDataStream />
            <Caption
              eyebrow="04"
              title="Sieben Tage Stoffwechsel"
              meta="endlos rotierend · Edge-Telemetry"
            />
          </BentoCell>

          <BentoCell className="col-span-12 lg:col-span-4" cardHeight="h-[300px]">
            <BentoFocusMode />
            <Caption
              eyebrow="05"
              title="Bio im Fokus"
              meta="Live-Tonalitätskontrolle · Entwurf 03"
            />
          </BentoCell>
        </div>
      </section>

      <Footer />
    </main>
  )
}

function TopBar({ username }: { username: string }) {
  return (
    <header className="sticky top-0 z-30 border-b border-slate-200/70 bg-[#f9fafb]/80 backdrop-blur">
      <div className="mx-auto flex max-w-[1400px] items-center justify-between px-6 py-4 md:px-10">
        <div className="flex items-center gap-3">
          <span className="grid size-7 place-items-center rounded-full bg-slate-900 text-white">
            <Sparkle size={12} weight="fill" />
          </span>
          <span className="font-display text-[15px] font-medium tracking-tight">
            Character Works
          </span>
          <span className="hidden font-mono text-[10px] tabular-nums text-slate-500 md:inline">
            v0.4.7
          </span>
        </div>
        <nav className="hidden items-center gap-7 text-[13px] text-slate-600 md:flex">
          <Link href="/dashboard" className="text-slate-900">
            Übersicht
          </Link>
          <Link href={`/${username}/cv`} className="hover:text-slate-900">
            CV-Modus
          </Link>
          <Link href="#" className="hover:text-slate-900">
            Persona
          </Link>
          <Link href="#" className="hover:text-slate-900">
            Stimme
          </Link>
        </nav>
        <div className="flex items-center gap-3">
          <span className="hidden font-mono text-[10px] tabular-nums text-slate-500 md:inline">
            @{username}
          </span>
          <span
            className="grid size-8 place-items-center rounded-full bg-gradient-to-br from-rose-200 via-amber-100 to-emerald-200 text-[11px] font-medium text-slate-800 ring-1 ring-inset ring-white/60"
            aria-hidden
          >
            {username.slice(0, 2).toUpperCase()}
          </span>
        </div>
      </div>
    </header>
  )
}

function Stat({
  label,
  value,
  delta,
}: {
  label: string
  value: string
  delta: string
}) {
  return (
    <div className="col-span-6 md:col-span-3">
      <p className="mb-2 text-[11px] uppercase tracking-[0.18em] text-slate-500">
        {label}
      </p>
      <p className="font-display text-[26px] leading-none tracking-tight tabular-nums text-slate-900">
        {value}
      </p>
      <p className="mt-1.5 font-mono text-[11px] tabular-nums text-slate-500">
        {delta}
      </p>
    </div>
  )
}

function BentoCell({
  className,
  cardHeight,
  children,
}: {
  className?: string
  cardHeight: string
  children: React.ReactNode
}) {
  const [card, caption] = Array.isArray(children) ? children : [children, null]
  return (
    <motion.div
      initial={{ opacity: 0, y: 18 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: '-80px' }}
      transition={{ type: 'spring', stiffness: 100, damping: 20 }}
      className={`flex flex-col gap-4 ${className ?? ''}`}
    >
      <div className={cardHeight}>{card}</div>
      {caption}
    </motion.div>
  )
}

function Caption({
  eyebrow,
  title,
  meta,
}: {
  eyebrow: string
  title: string
  meta: string
}) {
  return (
    <div className="flex items-baseline justify-between gap-4 px-2">
      <div>
        <span className="mr-3 font-mono text-[10px] tracking-[0.18em] text-slate-400">
          {eyebrow}
        </span>
        <span className="font-display text-[14.5px] font-medium tracking-tight text-slate-900">
          {title}
        </span>
      </div>
      <span className="text-right text-[11.5px] text-slate-500">{meta}</span>
    </div>
  )
}

function Footer() {
  return (
    <footer className="border-t border-slate-200/80">
      <div className="mx-auto flex max-w-[1400px] flex-col gap-4 px-6 py-10 text-[12px] text-slate-500 md:flex-row md:items-center md:justify-between md:px-10">
        <div className="flex items-center gap-3">
          <span className="font-display text-[13px] font-medium tracking-tight text-slate-700">
            Character Works
          </span>
          <span className="font-mono tabular-nums">— Berlin · 52.5200° N</span>
        </div>
        <div className="flex items-center gap-6">
          <span>Telemetry</span>
          <span>Privacy</span>
          <span className="font-mono tabular-nums">b1f4a3</span>
        </div>
      </div>
    </footer>
  )
}
