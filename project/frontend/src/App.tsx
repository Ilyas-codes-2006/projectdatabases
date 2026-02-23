import {useState} from 'react'
import './App.css'
import courtsBg from './assets/court.jpeg'


type View = 'home' | 'login' | 'register'

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

  const clearMessage = () => setMessage(null)

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
        setLoggedInUser(data.name)
        setView('home')
        setMessage({ text: `Welcome back, ${data.name}!`, type: 'success' })
      } else {
        setMessage({ text: data.error || 'Login failed', type: 'error' })
      }
    } catch {
      setMessage({ text: 'Could not connect to server', type: 'error' })
    } finally {
      setLoading(false)
    }
  }

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    clearMessage()
    if (registerData.password !== registerData.confirm_password) {
      setMessage({ text: 'Passwords do not match', type: 'error' })
      return
    }
    if (registerData.password.length < 8) {
      setMessage({ text: 'Password must be at least 8 characters', type: 'error' })
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
        setMessage({ text: 'Account created! You can now log in.', type: 'success' })
        setView('login')
      } else {
        setMessage({ text: data.error || 'Registration failed', type: 'error' })
      }
    } catch {
      setMessage({ text: 'Could not connect to server', type: 'error' })
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    setLoggedInUser(null)
    setMessage({ text: 'You have been logged out.', type: 'success' })
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

      {/* Home View */}
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

      {/* Login View */}
      {view === 'login' && (
        <div className="auth-wrapper">
          <div className="auth-card">
            <div className="auth-header">
              <span className="auth-icon">🎾</span>
              <h2>Welcome back</h2>
              <p>Sign in to your club account</p>
            </div>
            <form onSubmit={handleLogin} className="auth-form">
              <div className="form-group">
                <label>Email address</label>
                <input
                  type="email"
                  placeholder="you@example.com"
                  required
                  value={loginData.email}
                  onChange={e => setLoginData({ ...loginData, email: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Password</label>
                <input
                  type="password"
                  placeholder="Your password"
                  required
                  value={loginData.password}
                  onChange={e => setLoginData({ ...loginData, password: e.target.value })}
                />
              </div>
              <button type="submit" className="btn-submit" disabled={loading}>
                {loading ? 'Signing in…' : 'Sign In'}
              </button>
            </form>
            <p className="auth-switch">
              No account yet?{' '}
              <button onClick={() => { setView('register'); clearMessage() }}>Create one</button>
            </p>
          </div>
        </div>
      )}

      {/* Register View */}
      {view === 'register' && (
        <div className="auth-wrapper">
          <div className="auth-card auth-card-wide">
            <div className="auth-header">
              <span className="auth-icon">🏅</span>
              <h2>Join your club</h2>
              <p>Create your player profile</p>
            </div>
            <form onSubmit={handleRegister} className="auth-form">
              <div className="form-row">
                <div className="form-group">
                  <label>First name</label>
                  <input type="text" placeholder="Jan" required
                    value={registerData.first_name}
                    onChange={e => setRegisterData({ ...registerData, first_name: e.target.value })} />
                </div>
                <div className="form-group">
                  <label>Last name</label>
                  <input type="text" placeholder="Janssen" required
                    value={registerData.last_name}
                    onChange={e => setRegisterData({ ...registerData, last_name: e.target.value })} />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Email address</label>
                  <input type="email" placeholder="jan@example.com" required
                    value={registerData.email}
                    onChange={e => setRegisterData({ ...registerData, email: e.target.value })} />
                </div>
                <div className="form-group">
                  <label>Age</label>
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
                    <option value="both">Both</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Skill level</label>
                  <select required value={registerData.skill_level}
                    onChange={e => setRegisterData({ ...registerData, skill_level: e.target.value })}>
                    <option value="">Select level…</option>
                    {SKILL_LEVELS.map(l => <option key={l} value={l.toLowerCase()}>{l}</option>)}
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label>Club</label>
                <select required value={registerData.club}
                  onChange={e => setRegisterData({ ...registerData, club: e.target.value })}>
                  <option value="">Select your club…</option>
                  {CLUBS.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Password</label>
                  <input type="password" placeholder="Min. 8 characters" required
                    value={registerData.password}
                    onChange={e => setRegisterData({ ...registerData, password: e.target.value })} />
                </div>
                <div className="form-group">
                  <label>Confirm password</label>
                  <input type="password" placeholder="Repeat password" required
                    value={registerData.confirm_password}
                    onChange={e => setRegisterData({ ...registerData, confirm_password: e.target.value })} />
                </div>
              </div>

              <button type="submit" className="btn-submit" disabled={loading}>
                {loading ? 'Creating account…' : 'Create Account'}
              </button>
            </form>
            <p className="auth-switch">
              Already have an account?{' '}
              <button onClick={() => { setView('login'); clearMessage() }}>Sign in</button>
            </p>
          </div>
        </div>
      )}
    </div>
  )
}