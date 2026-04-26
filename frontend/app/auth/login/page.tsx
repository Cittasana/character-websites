'use client'
import { useState } from 'react'
import Link from 'next/link'
import { createClient } from '@/lib/supabase/client'
import { useRouter } from 'next/navigation'
import { getOnboardingStatus, ApiError } from '@/lib/api'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()
  const supabase = createClient()

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    const { data, error: signError } = await supabase.auth.signInWithPassword({
      email,
      password,
    })
    if (signError) {
      setError(signError.message)
      setLoading(false)
      return
    }
    const session = data.session
    if (!session) {
      setError('Keine Sitzung — bitte E-Mail bestätigen oder erneut versuchen.')
      setLoading(false)
      return
    }
    try {
      const status = await getOnboardingStatus(session.access_token)
      if (status.needs_onboarding) router.push('/onboarding')
      else router.push('/dashboard')
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        router.push('/auth/register')
        return
      }
      setError('Profil konnte nicht geladen werden.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main style={{ maxWidth: 400, margin: '80px auto', padding: '0 24px' }}>
      <h1>Anmelden</h1>
      <form onSubmit={handleLogin}>
        <input
          type="email"
          value={email}
          onChange={e => setEmail(e.target.value)}
          placeholder="E-Mail"
          required
          style={{ display: 'block', width: '100%', marginBottom: 12, padding: 8 }}
        />
        <input
          type="password"
          value={password}
          onChange={e => setPassword(e.target.value)}
          placeholder="Passwort"
          required
          style={{ display: 'block', width: '100%', marginBottom: 12, padding: 8 }}
        />
        {error && <p style={{ color: 'red' }}>{error}</p>}
        <button type="submit" disabled={loading} style={{ padding: '8px 24px' }}>
          {loading ? 'Wird angemeldet…' : 'Anmelden'}
        </button>
      </form>
      <p style={{ marginTop: 24 }}>
        <Link href="/auth/register">Noch kein Konto? Registrieren</Link>
      </p>
    </main>
  )
}
