'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Warning } from '@phosphor-icons/react'
import { createClient } from '@/lib/supabase/client'
import { getMe, getOnboardingStatus, ApiError } from '@/lib/api'
import { EditorialShell } from './_components/EditorialShell'

type LoadState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; username: string; needsOnboarding: boolean }

export default function DashboardPage() {
  const router = useRouter()
  const supabase = createClient()
  const [state, setState] = useState<LoadState>({ status: 'loading' })

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      const {
        data: { session },
      } = await supabase.auth.getSession()
      if (!session) {
        router.replace('/auth/login')
        return
      }
      try {
        const [me, status] = await Promise.all([
          getMe(session.access_token),
          getOnboardingStatus(session.access_token),
        ])
        if (cancelled) return
        setState({
          status: 'ready',
          username: me.username,
          needsOnboarding: status.needs_onboarding,
        })
      } catch (err) {
        if (cancelled) return
        if (err instanceof ApiError && err.status === 404) {
          router.replace('/auth/register')
          return
        }
        setState({
          status: 'error',
          message: 'Profil konnte nicht geladen werden.',
        })
      }
    })()
    return () => {
      cancelled = true
    }
  }, [router, supabase.auth])

  if (state.status === 'loading') return <DashboardSkeleton />
  if (state.status === 'error') return <DashboardError message={state.message} />

  return (
    <EditorialShell
      username={state.username}
      needsOnboarding={state.needsOnboarding}
    />
  )
}

function DashboardSkeleton() {
  return (
    <main className="min-h-[100dvh] bg-[#f9fafb]">
      <div className="border-b border-slate-200/70">
        <div className="mx-auto flex max-w-[1400px] items-center justify-between px-6 py-4 md:px-10">
          <div className="flex items-center gap-3">
            <ShimmerBox className="size-7 rounded-full" />
            <ShimmerBox className="h-4 w-36 rounded-md" />
          </div>
          <ShimmerBox className="size-8 rounded-full" />
        </div>
      </div>

      <section className="mx-auto grid max-w-[1400px] grid-cols-12 gap-8 px-6 pb-10 pt-16 md:px-10 md:pt-24 lg:pt-32">
        <div className="col-span-12 lg:col-span-5">
          <ShimmerBox className="mb-8 h-6 w-48 rounded-full" />
          <ShimmerBox className="mb-3 h-12 w-3/4 rounded-md" />
          <ShimmerBox className="mb-3 h-12 w-2/3 rounded-md" />
          <ShimmerBox className="mb-3 h-12 w-3/5 rounded-md" />
          <ShimmerBox className="h-12 w-1/3 rounded-md" />
        </div>
        <div className="col-span-12 mt-2 flex flex-col gap-4 lg:col-span-6 lg:col-start-7 lg:mt-0">
          <ShimmerBox className="h-4 w-full rounded-md" />
          <ShimmerBox className="h-4 w-11/12 rounded-md" />
          <ShimmerBox className="h-4 w-9/12 rounded-md" />
          <ShimmerBox className="mt-4 h-11 w-56 rounded-full" />
        </div>
      </section>

      <section className="mx-auto max-w-[1400px] px-6 pb-24 md:px-10">
        <div className="grid grid-cols-12 gap-6">
          {[360, 360, 360, 300, 300].map((h, i) => (
            <ShimmerBox
              key={i}
              className={`rounded-[2.5rem] ${
                i < 3
                  ? 'col-span-12 md:col-span-4'
                  : i === 3
                    ? 'col-span-12 lg:col-span-8'
                    : 'col-span-12 lg:col-span-4'
              }`}
              style={{ height: h }}
            />
          ))}
        </div>
      </section>
    </main>
  )
}

function ShimmerBox({
  className,
  style,
}: {
  className?: string
  style?: React.CSSProperties
}) {
  return (
    <div
      className={`relative overflow-hidden border border-slate-200/60 bg-slate-100/70 ${className ?? ''}`}
      style={style}
    >
      <div className="absolute inset-0 animate-[shimmer_1.6s_linear_infinite] bg-[linear-gradient(110deg,transparent_30%,rgba(255,255,255,0.6)_50%,transparent_70%)] bg-[length:200%_100%]" />
    </div>
  )
}

function DashboardError({ message }: { message: string }) {
  return (
    <main className="grid min-h-[100dvh] place-items-center bg-[#f9fafb] px-6">
      <div className="w-full max-w-md rounded-[2rem] border border-rose-200/70 bg-white p-10 text-center shadow-[0_20px_40px_-15px_rgba(244,63,94,0.18)]">
        <span className="mx-auto mb-5 grid size-12 place-items-center rounded-full bg-rose-50 text-rose-600">
          <Warning size={20} weight="bold" />
        </span>
        <h2 className="font-display text-[22px] font-medium tracking-tight text-slate-900">
          Profil nicht erreichbar
        </h2>
        <p className="mt-2 text-[14px] leading-relaxed text-slate-600">
          {message}
        </p>
        <Link
          href="/auth/login"
          className="mt-6 inline-flex items-center gap-2 rounded-full bg-slate-900 px-5 py-2.5 text-[13px] font-medium text-white transition hover:bg-slate-800 active:translate-y-[1px]"
        >
          Erneut anmelden
        </Link>
      </div>
    </main>
  )
}
