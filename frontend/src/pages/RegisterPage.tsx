import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

interface User {
  first_name: string
  last_name: string
  email: string
  date_of_birth: string
  password: string
  confirm_password: string
}

interface Props {
  onSuccess: () => void
  onNavigate: (path: string) => void
  setMessage: (msg: { text: string; type: 'error' | 'success' } | null) => void
}

export default function RegisterPage({ onSuccess, onNavigate, setMessage }: Props) {
  const navigate = useNavigate()
  const [registerData, setRegisterData] = useState<User>({
    first_name: '',
    last_name: '',
    email: '',
    date_of_birth: '',
    password: '',
    confirm_password: '',
  })
  const [loading, setLoading] = useState(false)

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    setMessage(null)
    if (registerData.password !== registerData.confirm_password) {
      setMessage({ text: 'Wachtwoorden komen niet overeen', type: 'error' })
      return
    }
    if (registerData.password.length < 8) {
      setMessage({ text: 'Wachtwoord moet minimaal 8 tekens bevatten', type: 'error' })
      return
    }
    setLoading(true)
    try {
      const res = await fetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(registerData),
      })
      const data = await res.json()
      if (res.ok) {
        onSuccess()
      } else {
        if (res.status === 500) return navigate('/500')
        if (res.status === 502 || res.status === 503) return navigate('/502')
        setMessage({ text: data.error || 'Registratie mislukt', type: 'error' })
      }
    } catch {
      navigate('/502')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-wrapper">
      <div className="auth-card auth-card-wide">
        <div className="auth-header">
          <span className="auth-icon">🏅</span>
          <h2>Word lid van je club</h2>
          <p>Maak je spelersprofiel aan</p>
        </div>

        <form onSubmit={handleRegister} className="auth-form">
          <div className="form-row">
            <div className="form-group">
              <label>Voornaam</label>
              <input
                type="text"
                placeholder="Jan"
                required
                value={registerData.first_name}
                onChange={e => setRegisterData({ ...registerData, first_name: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label>Achternaam</label>
              <input
                type="text"
                placeholder="Janssen"
                required
                value={registerData.last_name}
                onChange={e => setRegisterData({ ...registerData, last_name: e.target.value })}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>E-mailadres</label>
              <input
                type="email"
                placeholder="jan@voorbeeld.com"
                required
                value={registerData.email}
                onChange={e => setRegisterData({ ...registerData, email: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label>Geboortedatum</label>
              <input
                type="date"
                required
                value={registerData.date_of_birth}
                onChange={e => setRegisterData({ ...registerData, date_of_birth: e.target.value })}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>Wachtwoord</label>
              <input
                type="password"
                placeholder="Min. 8 tekens"
                required
                value={registerData.password}
                onChange={e => setRegisterData({ ...registerData, password: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label>Bevestig wachtwoord</label>
              <input
                type="password"
                placeholder="Herhaal wachtwoord"
                required
                value={registerData.confirm_password}
                onChange={e => setRegisterData({ ...registerData, confirm_password: e.target.value })}
              />
            </div>
          </div>

          <button type="submit" className="btn-submit" disabled={loading}>
            {loading ? 'Account aanmaken…' : 'Account aanmaken'}
          </button>
        </form>

        <p className="auth-switch">
          Al een account?{' '}
          <button onClick={() => onNavigate('/login')}>Inloggen</button>
        </p>
      </div>
    </div>
  )
}