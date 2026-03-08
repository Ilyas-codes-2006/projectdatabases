import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

interface Props {
  onSuccess: (name: string, token: string, is_admin: boolean) => void
  onNavigate: (path: string) => void
  setMessage: (msg: { text: string; type: 'error' | 'success' } | null) => void
}

export default function LoginPage({ onSuccess, onNavigate, setMessage }: Props) {
  const navigate = useNavigate()
  const [loginData, setLoginData] = useState({ email: '', password: '' })
  const [loading, setLoading] = useState(false)

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setMessage(null)
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(loginData),
      })
      const data = await res.json()
      if (res.ok) {
        onSuccess(data.name, data.token, data.is_admin ?? false)
      } else {
        if (res.status === 404) return navigate('*')
        if (res.status === 500) return navigate('/500')
        if (res.status === 502 || res.status === 503) return navigate('/502')
        setMessage({ text: data.error || 'Inloggen mislukt', type: 'error' })
      }
    } catch {
      navigate('/502')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-wrapper">
      <div className="auth-card">
        <div className="auth-header">
          <span className="auth-icon">🎾</span>
          <h2>Welkom terug</h2>
          <p>Log in op je clubaccount</p>
        </div>

        <form onSubmit={handleLogin} className="auth-form">
          <div className="form-group">
            <label>E-mailadres</label>
            <input
              type="email"
              placeholder="jij@voorbeeld.com"
              required
              value={loginData.email}
              onChange={e => setLoginData({ ...loginData, email: e.target.value })}
            />
          </div>
          <div className="form-group">
            <label>Wachtwoord</label>
            <input
              type="password"
              placeholder="Jouw wachtwoord"
              required
              value={loginData.password}
              onChange={e => setLoginData({ ...loginData, password: e.target.value })}
            />
          </div>
          <button type="submit" className="btn-submit" disabled={loading}>
            {loading ? 'Inloggen…' : 'Inloggen'}
          </button>
        </form>

        <p className="auth-switch">
          <button onClick={() => onNavigate('/forgot-password')}>
            Wachtwoord vergeten?
          </button>
        </p>
        <p className="auth-switch">
          Nog geen account?{' '}
          <button onClick={() => onNavigate('/register')}>Maak er een aan</button>
        </p>
      </div>
    </div>
  )
}