import { useState } from 'react'

interface Props {
  onNavigate: (path: string) => void
  setMessage: (msg: { text: string; type: 'error' | 'success' } | null) => void
}

export default function ForgotPasswordPage({ onNavigate, setMessage }: Props) {
  const [forgotEmail, setForgotEmail] = useState('')
  const [loading, setLoading] = useState(false)

  const handleForgotPassword = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setMessage(null)
    try {
      const res = await fetch('/api/auth/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: forgotEmail }),
      })
      const data = await res.json()
      // Toon altijd de server-boodschap (die is altijd neutraal)
      setMessage({ text: data.message || data.error, type: res.ok ? 'success' : 'error' })
      if (res.ok) {
        setForgotEmail('')
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
          <span className="auth-icon">🔑</span>
          <h2>Wachtwoord vergeten</h2>
          <p>Vul je e-mailadres in. Als het bij ons bekend is, sturen we je een resetlink.</p>
        </div>

        <form onSubmit={handleForgotPassword} className="auth-form">
          <div className="form-group">
            <label>E-mailadres</label>
            <input
              type="email"
              placeholder="jij@voorbeeld.com"
              required
              value={forgotEmail}
              onChange={e => setForgotEmail(e.target.value)}
            />
          </div>
          <button type="submit" className="btn-submit" disabled={loading}>
            {loading ? 'Versturen…' : 'Stuur resetlink'}
          </button>
        </form>

        <p className="auth-switch">
          <button onClick={() => onNavigate('/login')}>
            ← Terug naar inloggen
          </button>
        </p>
      </div>
    </div>
  )
}