import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'

interface Props {
  onNavigate: (path: string) => void
  setMessage: (msg: { text: string; type: 'error' | 'success' } | null) => void
}

export default function ResetPasswordPage({ onNavigate, setMessage }: Props) {
  const [searchParams] = useSearchParams()
  const resetToken = searchParams.get('token') ?? ''

  const [resetPassword, setResetPassword] = useState('')
  const [resetConfirm, setResetConfirm] = useState('')
  const [loading, setLoading] = useState(false)

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault()
    setMessage(null)
    if (resetPassword !== resetConfirm) {
      setMessage({ text: 'Wachtwoorden komen niet overeen', type: 'error' })
      return
    }
    if (resetPassword.length < 8) {
      setMessage({ text: 'Wachtwoord moet minimaal 8 tekens bevatten', type: 'error' })
      return
    }
    setLoading(true)
    try {
      const res = await fetch('/api/auth/reset-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: resetToken, new_password: resetPassword }),
      })
      const data = await res.json()
      if (res.ok) {
        setMessage({ text: data.message, type: 'success' })
        setResetPassword('')
        setResetConfirm('')
        onNavigate('/login')
      } else {
        setMessage({ text: data.error, type: 'error' })
      }
    } catch {
      setMessage({ text: 'Kan geen verbinding maken met de server', type: 'error' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-wrapper">
      <div className="auth-card">
        <div className="auth-header">
          <span className="auth-icon">🔒</span>
          <h2>Nieuw wachtwoord instellen</h2>
          <p>Kies een sterk wachtwoord van minimaal 8 tekens.</p>
        </div>

        {resetToken ? (
          <form onSubmit={handleResetPassword} className="auth-form">
            <div className="form-group">
              <label>Nieuw wachtwoord</label>
              <input
                type="password"
                placeholder="Min. 8 tekens"
                required
                value={resetPassword}
                onChange={e => setResetPassword(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label>Bevestig wachtwoord</label>
              <input
                type="password"
                placeholder="Herhaal wachtwoord"
                required
                value={resetConfirm}
                onChange={e => setResetConfirm(e.target.value)}
              />
            </div>
            <button type="submit" className="btn-submit" disabled={loading}>
              {loading ? 'Opslaan…' : 'Wachtwoord instellen'}
            </button>
          </form>
        ) : (
          <p style={{ textAlign: 'center', color: 'var(--text-muted)', marginTop: '1rem' }}>
            Geen geldige resetlink gevonden. Vraag een nieuwe aan via "Wachtwoord vergeten".
          </p>
        )}

        <p className="auth-switch">
          <button onClick={() => onNavigate('/login')}>
            ← Terug naar inloggen
          </button>
        </p>
      </div>
    </div>
  )
}