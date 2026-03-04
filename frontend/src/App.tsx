import { useState, useEffect } from 'react'
import './App.css'
import courtsBg from './assets/court.jpeg'

// View types uitgebreid met de twee nieuwe schermen
type View = 'home' | 'login' | 'register' | 'forgot-password' | 'reset-password'

interface User {
  first_name: string
  last_name: string
  email: string
  age: string
  club: string
  sport: string
  skill_level: string
  password: string
  confirm_password: string
}

const CLUBS = [
  'TC De Warande',
  'TC Leuven',
  'Padel Factory Antwerp',
  'TC Sportoase',
  'Royal Bruges TC',
  'Other',
]

const SKILL_LEVELS = ['Beginner', 'Intermediate', 'Advanced', 'Competitive', 'Professional']

export default function App() {
  const [view, setView] = useState<View>('home')
  const [loginData, setLoginData] = useState({ email: '', password: '' })
  const [registerData, setRegisterData] = useState<User>({
    first_name: '', last_name: '', email: '', age: '',
    club: '', sport: 'tennis', skill_level: '', password: '', confirm_password: '',
  })
  const [message, setMessage] = useState<{ text: string; type: 'error' | 'success' } | null>(null)
  const [loggedInUser, setLoggedInUser] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  // Wachtwoord vergeten
  const [forgotEmail, setForgotEmail] = useState('')

  // Wachtwoord resetten
  const [resetToken, setResetToken] = useState('')
  const [resetPassword, setResetPassword] = useState('')
  const [resetConfirm, setResetConfirm] = useState('')

  // Restore session from localStorage on mount
  // Controleer ook of er een reset-token in de URL staat
  useEffect(() => {
    const token = localStorage.getItem('token')
    const name = localStorage.getItem('userName')
    if (token && name) {
      setLoggedInUser(name)
    }

    // Detecteer ?token=...&view=reset-password in de URL
    const params = new URLSearchParams(window.location.search)
    const urlToken = params.get('token')
    const urlView = params.get('view')
    if (urlToken && urlView === 'reset-password') {
      setResetToken(urlToken)
      setView('reset-password')
      // Verwijder de token uit de URL-balk (netter en veiliger)
      window.history.replaceState({}, '', '/')
    }
  }, [])

  const clearMessage = () => setMessage(null)

  // ---------------------------------------------------------------------------
  // Login
  // ---------------------------------------------------------------------------
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    clearMessage()
    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(loginData),
      })
      const data = await res.json()
      if (res.ok) {
        localStorage.setItem('token', data.token)
        localStorage.setItem('userName', data.name)
        setLoggedInUser(data.name)
        setView('home')
        setMessage({ text: `Welkom terug, ${data.name}!`, type: 'success' })
      } else {
        setMessage({ text: data.error || 'Inloggen mislukt', type: 'error' })
      }
    } catch {
      setMessage({ text: 'Kan geen verbinding maken met de server', type: 'error' })
    } finally {
      setLoading(false)
    }
  }

  // ---------------------------------------------------------------------------
  // Register
  // ---------------------------------------------------------------------------
  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    clearMessage()
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
        setMessage({ text: 'Account aangemaakt! Je kunt nu inloggen.', type: 'success' })
        setView('login')
      } else {
        setMessage({ text: data.error || 'Registratie mislukt', type: 'error' })
      }
    } catch {
      setMessage({ text: 'Kan geen verbinding maken met de server', type: 'error' })
    } finally {
      setLoading(false)
    }
  }

  // ---------------------------------------------------------------------------
  // Logout
  // ---------------------------------------------------------------------------
  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('userName')
    setLoggedInUser(null)
    setMessage({ text: 'Je bent uitgelogd.', type: 'success' })
  }

  // ---------------------------------------------------------------------------
  // Wachtwoord vergeten — stap 1: e-mail invullen
  // ---------------------------------------------------------------------------
  const handleForgotPassword = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    clearMessage()
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

  // ---------------------------------------------------------------------------
  // Wachtwoord resetten — stap 2: nieuw wachtwoord instellen
  // ---------------------------------------------------------------------------
  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault()
    clearMessage()
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
        setResetToken('')
        setView('login')
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
    <div className="app">
      {/* Navigation */}
      <nav className="navbar">
        <div className="nav-brand" onClick={() => setView('home')}>
          <span className="nav-logo">🎾</span>
          <span className="nav-title">MatchUp</span>
        </div>
        <div className="nav-links">
          <button className={`nav-btn ${view === 'home' ? 'active' : ''}`} onClick={() => setView('home')}>Home</button>
          {!loggedInUser ? (
            <>
              <button className={`nav-btn ${view === 'login' ? 'active' : ''}`} onClick={() => { setView('login'); clearMessage() }}>Login</button>
              <button className="nav-btn nav-cta" onClick={() => { setView('register'); clearMessage() }}>Join Now</button>
            </>
          ) : (
            <>
              <span className="nav-user">👋 {loggedInUser}</span>
              <button className="nav-btn" onClick={handleLogout}>Logout</button>
            </>
          )}
        </div>
      </nav>

      {/* Message Banner */}
      {message && (
        <div className={`message-banner ${message.type}`} onClick={clearMessage}>
          {message.text} <span className="message-close">×</span>
        </div>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* Home View                                                           */}
      {/* ------------------------------------------------------------------ */}
      {view === 'home' && (
        <main className="hero">
          <div className="hero-bg" style={{ backgroundImage: `url(${courtsBg})` }}></div>
          <div className="hero-content">
            <p className="hero-eyebrow">Your Club. Your Game.</p>
            <h1 className="hero-title">
              Manage your tennis &<br />padel experience
            </h1>
            <p className="hero-subtitle">
              Book courts, track your progress, connect with fellow players — all in one place for your club.
            </p>
            {!loggedInUser ? (
              <div className="hero-actions">
                <button className="btn-primary" onClick={() => { setView('register'); clearMessage() }}>Get Started</button>
                <button className="btn-secondary" onClick={() => { setView('login'); clearMessage() }}>Sign In</button>
              </div>
            ) : (
              <div className="hero-actions">
                <button className="btn-primary">Book a Court</button>
                <button className="btn-secondary">View Schedule</button>
              </div>
            )}
          </div>

          {/* Feature cards */}
          <div className="features">
            <div className="feature-card">
              <span className="feature-icon">🏆</span>
              <h3>Track Progress</h3>
              <p>Monitor your skill development and match history over time.</p>
            </div>
            <div className="feature-card">
              <span className="feature-icon">📅</span>
              <h3>Easy Booking</h3>
              <p>Reserve courts at your club in seconds, any time of day.</p>
            </div>
            <div className="feature-card">
              <span className="feature-icon">🤝</span>
              <h3>Find Partners</h3>
              <p>Match with players at your level and grow the community.</p>
            </div>
          </div>
        </main>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* Login View                                                          */}
      {/* ------------------------------------------------------------------ */}
      {view === 'login' && (
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

            {/* Wachtwoord vergeten link */}
            <p className="auth-switch">
              <button onClick={() => { setView('forgot-password'); clearMessage() }}>
                Wachtwoord vergeten?
              </button>
            </p>

            <p className="auth-switch">
              Nog geen account?{' '}
              <button onClick={() => { setView('register'); clearMessage() }}>Maak er een aan</button>
            </p>
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* Wachtwoord vergeten View                                            */}
      {/* ------------------------------------------------------------------ */}
      {view === 'forgot-password' && (
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
              <button onClick={() => { setView('login'); clearMessage() }}>
                ← Terug naar inloggen
              </button>
            </p>
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* Wachtwoord resetten View (via link in e-mail)                       */}
      {/* ------------------------------------------------------------------ */}
      {view === 'reset-password' && (
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
              <button onClick={() => { setView('login'); clearMessage() }}>
                ← Terug naar inloggen
              </button>
            </p>
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* Register View                                                       */}
      {/* ------------------------------------------------------------------ */}
      {view === 'register' && (
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
                  <input type="text" placeholder="Jan" required
                    value={registerData.first_name}
                    onChange={e => setRegisterData({ ...registerData, first_name: e.target.value })} />
                </div>
                <div className="form-group">
                  <label>Achternaam</label>
                  <input type="text" placeholder="Janssen" required
                    value={registerData.last_name}
                    onChange={e => setRegisterData({ ...registerData, last_name: e.target.value })} />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>E-mailadres</label>
                  <input type="email" placeholder="jan@voorbeeld.com" required
                    value={registerData.email}
                    onChange={e => setRegisterData({ ...registerData, email: e.target.value })} />
                </div>
                <div className="form-group">
                  <label>Leeftijd</label>
                  <input type="number" placeholder="25" min="6" max="100" required
                    value={registerData.age}
                    onChange={e => setRegisterData({ ...registerData, age: e.target.value })} />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Sport</label>
                  <select required value={registerData.sport}
                    onChange={e => setRegisterData({ ...registerData, sport: e.target.value })}>
                    <option value="tennis">Tennis</option>
                    <option value="padel">Padel</option>
                    <option value="both">Beide</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Niveau</label>
                  <select required value={registerData.skill_level}
                    onChange={e => setRegisterData({ ...registerData, skill_level: e.target.value })}>
                    <option value="">Kies niveau…</option>
                    {SKILL_LEVELS.map(l => <option key={l} value={l.toLowerCase()}>{l}</option>)}
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label>Club</label>
                <select required value={registerData.club}
                  onChange={e => setRegisterData({ ...registerData, club: e.target.value })}>
                  <option value="">Kies je club…</option>
                  {CLUBS.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Wachtwoord</label>
                  <input type="password" placeholder="Min. 8 tekens" required
                    value={registerData.password}
                    onChange={e => setRegisterData({ ...registerData, password: e.target.value })} />
                </div>
                <div className="form-group">
                  <label>Bevestig wachtwoord</label>
                  <input type="password" placeholder="Herhaal wachtwoord" required
                    value={registerData.confirm_password}
                    onChange={e => setRegisterData({ ...registerData, confirm_password: e.target.value })} />
                </div>
              </div>

              <button type="submit" className="btn-submit" disabled={loading}>
                {loading ? 'Account aanmaken…' : 'Account aanmaken'}
              </button>
            </form>
            <p className="auth-switch">
              Al een account?{' '}
              <button onClick={() => { setView('login'); clearMessage() }}>Inloggen</button>
            </p>
          </div>
        </div>
      )}
    </div>
  )
}