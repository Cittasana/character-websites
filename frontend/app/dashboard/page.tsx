'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'
import { getMe, getOnboardingStatus, ApiError } from '@/lib/api'

export default function DashboardPage() {
  const router = useRouter()
  const supabase = createClient()
  const [username, setUsername] = useState<string | null>(null)
  const [needsOnboarding, setNeedsOnboarding] = useState(false)
  const [error, setError] = useState<string | null>(null)

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
        setUsername(me.username)
        setNeedsOnboarding(status.needs_onboarding)
      } catch (err) {
        if (cancelled) return
        if (err instanceof ApiError && err.status === 404) {
          router.replace('/auth/register')
          return
        }
        setError('Profil konnte nicht geladen werden.')
      }
    })()
    return () => {
      cancelled = true
    }
  }, [router, supabase.auth])

  if (error) {
    return (
      <main style={{ maxWidth: 520, margin: '80px auto', padding: '0 24px' }}>
        <p style={{ color: 'red' }}>{error}</p>
      </main>
    )
  }

  if (!username) {
    return (
      <main style={{ maxWidth: 520, margin: '80px auto', padding: '0 24px' }}>
        <p>Laden…</p>
      </main>
    )
  }

  return (
    <main style={{ maxWidth: 520, margin: '80px auto', padding: '0 24px' }}>
      <h1>Dashboard</h1>
      {needsOnboarding ? (
        <p style={{ marginTop: 16 }}>
          Dein Konto ist noch nicht fertig eingerichtet.{' '}
          <Link href="/onboarding">Zum Onboarding</Link>
        </p>
      ) : (
        <>
          <p style={{ marginTop: 16, color: '#64748b' }}>
            Öffentliche Seite (CV-Modus):
          </p>
          <p style={{ marginTop: 8 }}>
            <Link href={`/${username}/cv`}>/{username}/cv</Link>
          </p>
        </>
      )}
      <p style={{ marginTop: 24 }}>
        <Link href="/">Zur Startseite</Link>
      </p>
    </main>
  )
}
