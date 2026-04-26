'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'
import { registerAccount, ApiError } from '@/lib/api'

export default function RegisterPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()
  const supabase = createClient()

  async function handleRegister(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const tokens = await registerAccount({
        email,
        password,
        full_name: fullName.trim() || null,
      })
      const { error: sessionError } = await supabase.auth.setSession({
        access_token: tokens.access_token,
        refresh_token: tokens.refresh_token,
      })
      if (sessionError) {
        setError(sessionError.message)
        return
      }
      router.push('/onboarding')
    } catch (err) {
      if (err instanceof ApiError) setError(err.message)
      else setError('Registrierung fehlgeschlagen.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main style={{ maxWidth: 400, margin: '80px auto', padding: '0 24px' }}>
      <h1>Konto anlegen</h1>
      <p style={{ color: '#64748b', marginBottom: '1.5rem' }}>
        Danach richtest du deinen öffentlichen Nutzernamen und deine erste Website ein.
      </p>
      <form onSubmit={handleRegister}>
        <input
          type="text"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          placeholder="Anzeigename (optional)"
          style={{ display: 'block', width: '100%', marginBottom: 12, padding: 8 }}
        />
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="E-Mail"
          required
          style={{ display: 'block', width: '100%', marginBottom: 12, padding: 8 }}
        />
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Passwort (mind. 8 Zeichen)"
          required
          minLength={8}
          style={{ display: 'block', width: '100%', marginBottom: 12, padding: 8 }}
        />
        {error && <p style={{ color: 'red' }}>{error}</p>}
        <button type="submit" disabled={loading} style={{ padding: '8px 24px' }}>
          {loading ? 'Wird angelegt…' : 'Registrieren'}
        </button>
      </form>
      <p style={{ marginTop: 24 }}>
        <Link href="/auth/login">Bereits ein Konto? Anmelden</Link>
      </p>
    </main>
  )
}
