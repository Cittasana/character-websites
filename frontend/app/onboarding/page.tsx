'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'
import {
  completeOnboarding,
  getOnboardingStatus,
  ApiError,
} from '@/lib/api'

export default function OnboardingPage() {
  const router = useRouter()
  const supabase = createClient()
  const [ready, setReady] = useState(false)
  const [username, setUsername] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [loading, setLoading] = useState(false)
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
        const status = await getOnboardingStatus(session.access_token)
        if (cancelled) return
        if (!status.needs_onboarding) {
          router.replace('/dashboard')
          return
        }
        setUsername(status.username?.startsWith('cwtmp_') ? '' : status.username || '')
        setDisplayName(status.display_name || '')
        setReady(true)
      } catch {
        if (!cancelled) router.replace('/auth/login')
      }
    })()
    return () => {
      cancelled = true
    }
  }, [router, supabase.auth])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    const {
      data: { session },
    } = await supabase.auth.getSession()
    if (!session) {
      router.replace('/auth/login')
      return
    }
    try {
      const u = username.trim().toLowerCase()
      const d = displayName.trim()
      if (!u || !d) {
        setError('Bitte Nutzernamen und Anzeigenamen ausfüllen.')
        setLoading(false)
        return
      }
      const result = await completeOnboarding(session.access_token, {
        username: u,
        display_name: d,
      })
      router.push(`/${result.username}/cv`)
    } catch (err) {
      if (err instanceof ApiError) setError(err.message)
      else setError('Speichern fehlgeschlagen.')
    } finally {
      setLoading(false)
    }
  }

  if (!ready) {
    return (
      <main style={{ maxWidth: 480, margin: '80px auto', padding: '0 24px' }}>
        <p>Laden…</p>
      </main>
    )
  }

  return (
    <main style={{ maxWidth: 480, margin: '80px auto', padding: '0 24px' }}>
      <h1>Willkommen</h1>
      <p style={{ color: '#64748b', marginBottom: '1.5rem' }}>
        Wähle deinen öffentlichen Nutzernamen (URL:{' '}
        <strong>nutzername</strong>.characterwebsites.com) und wie du angezeigt werden möchtest.
      </p>
      <form onSubmit={handleSubmit}>
        <label style={{ display: 'block', marginBottom: 8, fontWeight: 600 }}>
          Nutzername
        </label>
        <input
          value={username}
          onChange={(e) => setUsername(e.target.value.toLowerCase())}
          placeholder="z. B. alex-m"
          required
          pattern="[a-z][a-z0-9-]{1,28}[a-z0-9]"
          title="Kleinbuchstaben, Zahlen und Bindestrich, 3–30 Zeichen"
          style={{ display: 'block', width: '100%', marginBottom: 16, padding: 8 }}
        />
        <label style={{ display: 'block', marginBottom: 8, fontWeight: 600 }}>
          Anzeigename
        </label>
        <input
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
          placeholder="Wie soll dein Name auf der Seite erscheinen?"
          required
          style={{ display: 'block', width: '100%', marginBottom: 16, padding: 8 }}
        />
        {error && <p style={{ color: 'red', marginBottom: 12 }}>{error}</p>}
        <button type="submit" disabled={loading} style={{ padding: '10px 24px' }}>
          {loading ? 'Wird gespeichert…' : 'Website einrichten'}
        </button>
      </form>
      <p style={{ marginTop: 24 }}>
        <Link href="/dashboard">Zum Dashboard</Link>
      </p>
    </main>
  )
}
