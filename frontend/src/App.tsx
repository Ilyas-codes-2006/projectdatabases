import {useState, useEffect} from 'react'
import './App.css'
import courtsBg from './assets/court.jpeg'


type View = 'home' | 'login' | 'register' | 'teams' | 'clubs' | 'joinTeams'

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
  const [teams, setTeams] = useState<any[]>([])
  const [teamsLoading, setTeamsLoading] = useState(false)
  const [newTeamName, setNewTeamName] = useState('')
  const [clubs, setClubs] = useState<any[]>([])
  const [clubsLoading, setClubsLoading] = useState(false)
  const [userClub, setUserClub] = useState<number | null>(null)

  // Restore session from localStorage on mount
  useEffect(() => {
    const token = localStorage.getItem('token')
    const name = localStorage.getItem('userName')
    if (token && name) {
      setLoggedInUser(name)
    }
  }, [])
  const fetchTeams = async () => {
    console.debug("Fetching teams…")
    setTeamsLoading(true)
    try {
      const res = await fetch('/api/teams', {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      })
      const data = await res.json()
      console.debug("Teams fetched:", data)
      if (data.success) setTeams(data.teams)
    } catch (err) {
      console.error("Error fetching teams:", err)
    } finally {
      setTeamsLoading(false)
    }
  }
  useEffect(() => {
    if (view === 'teams' || view === 'joinTeams') {
      fetchTeams()
    }
  }, [view])

  useEffect(() => {
    if (view === 'clubs') {
      setClubsLoading(true)
      setClubs([
        { id: 1, name: 'TC De Warande', city: 'Brussel', sports: ['tennis'] },
        { id: 2, name: 'Padel Factory Antwerp', city: 'Antwerpen', sports: ['padel'] },
        { id: 3, name: 'TC Sportoase', city: 'Gent', sports: ['tennis', 'padel'] },
      ])
      setClubsLoading(false)
    }
  }, [view])

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
        localStorage.setItem('token', data.token)
        localStorage.setItem('userName', data.name)
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
    localStorage.removeItem('token')
    localStorage.removeItem('userName')
    setLoggedInUser(null)
    setMessage({ text: 'You have been logged out.', type: 'success' })
  }

  const handleCreateTeam = async () => {
    if (!newTeamName) return
    setLoading(true)
    clearMessage()

    try {
      const res = await fetch('/api/teams', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ team_name: newTeamName })
      })

      const data = await res.json()

      if (!data.success) {
        if (data.error === "already_in_team") {
          setMessage({ text: "Already in a team!", type: "error" })
        } else if (data.error === "no_active_ladder") {
          setMessage({ text: "No active ladder found", type: "error" })
        } else {
          setMessage({ text: data.error || "Failed to create team", type: "error" })
        }
      } else {
        if (data.message === "team_created") {
          setMessage({ text: "Team created!", type: "success" })
          setNewTeamName('')
          await fetchTeams()
        }
      }

    } catch {
      setMessage({ text: "Could not connect to server", type: "error" })
    } finally {
      setLoading(false)
    }
  }

  const handleJoinTeam = async (team_id: number) => {
    setLoading(true)
    clearMessage()

    try {
      const res = await fetch(`/api/teams/${team_id}/join`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      })

      const data = await res.json()

      if (!data.success) {
        if (data.error === "already_in_team") {
          setMessage({ text: "Already in a team!", type: "error" })
        } else if (data.error === "team_full") {
          setMessage({ text: "This team is already full", type: "error" })
        } else if (data.error === "team_not_found") {
          setMessage({ text: "Team not found", type: "error" })
        } else {
          setMessage({ text: data.error || "Failed to join team", type: "error" })
        }
      } else {
        // Success
        if (data.message === "joined_team") {
          setMessage({ text: "You joined the team!", type: "success" })
          await fetchTeams()
        }
      }

    } catch {
      setMessage({ text: "Could not connect to server", type: "error" })
    } finally {
      setLoading(false)
    }
  }
  const handleJoinClub = async (club_id: number) => {
    setLoading(true)
    clearMessage()
    try {
      const res = await fetch(`/api/clubs/${club_id}/join`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      })
      const data = await res.json()
      if (res.ok) {
        setMessage({ text: 'Successfully joined the club!', type: 'success' })
        setUserClub(club_id)
      } else {
        setMessage({ text: data.error || 'Failed to join club', type: 'error' })
      }
    } catch {
      setMessage({ text: 'Could not connect to server', type: 'error' })
    } finally {
      setLoading(false)
    }
  }

  const handleLeaveClub = async () => {
    setLoading(true)
    clearMessage()
    try {
      const res = await fetch('/api/clubs/leave', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      })
      const data = await res.json()
      if (res.ok) {
        setMessage({ text: 'Successfully left the club!', type: 'success' })
        setUserClub(null)
      } else {
        setMessage({ text: data.error || 'Failed to leave club', type: 'error' })
      }
    } catch {
      setMessage({ text: 'Could not connect to server', type: 'error' })
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
              <button className={`nav-btn ${view === 'teams' ? 'active' : ''}`} onClick={() => setView('teams')}>My Team</button>
              <button className={`nav-btn ${view === 'clubs' ? 'active' : ''}`} onClick={() => setView('clubs')}>Clubs</button>
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
      {/* Teams View */}
      {view === 'teams' && (
        <div className="auth-wrapper">
          <div className="auth-card auth-card-wide">

            <div className="auth-header">
              <span className="auth-icon">🏸</span>
              <h2>Padel Teams</h2>
              <p>Create your own team or join another</p>
            </div>

            {/* Join team button */}
            <div style={{display:'flex', justifyContent:'center', marginBottom:'2rem'}}>
              <button
                className="btn-primary"
                onClick={() => setView('joinTeams')}
              >
                Join a Team
              </button>
            </div>

            {/* Create team */}
            <div className="auth-form">

              <div className="form-group">
                <label>Create a new team</label>

                <input
                  type="text"
                  placeholder="Team name…"
                  value={newTeamName}
                  onChange={e => setNewTeamName(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleCreateTeam()
                  }}
                />
              </div>
              <button
                className="btn-submit"
                onClick={handleCreateTeam}
                disabled={loading || !newTeamName}
              >
                {loading ? 'Creating…' : 'Create Team'}
              </button>
            </div>
          </div>
        </div>
      )}
      {/* Join Teams Page */}
      {view === 'joinTeams' && (
        <div className="auth-wrapper">
          <div className="auth-card auth-card-wide">
            <div className="auth-header">
              <span className="auth-icon">👥</span>
              <h2>Available Teams</h2>
              <p>Join an existing team</p>
            </div>
            {teamsLoading ? (
              <p style={{ color: 'var(--text-muted)', textAlign: 'center' }}>
                Loading teams…
              </p>
            ) : (
              <div style={{ display:'flex', flexDirection:'column', gap:'1rem' }}>
                {teams.length === 0 && (
                  <p style={{ color: 'var(--text-muted)', textAlign: 'center' }}>
                    No teams available yet
                  </p>
                )}
                {teams.map((team:any) => (
                  <div
                    key={team.team_id}
                    className="feature-card"
                    style={{
                      display:'flex',
                      justifyContent:'space-between',
                      alignItems:'center'
                    }}
                  >
                    <div>
                      <strong>{team.team_name}</strong>
                      <p style={{
                        color:'var(--text-muted)',
                        fontSize:'0.85rem',
                        marginTop:'4px'
                      }}>
                        {team.member_count}/2 players
                        {team.member_count >= 2 ? 'Full' : 'Open'}
                      </p>

                    </div>
                    {team.member_count < 2 ? (
                      <button
                        className="btn-primary"
                        onClick={() => handleJoinTeam(team.team_id)}
                        style={{padding:'8px 20px', fontSize:'0.9rem'}}
                      >
                        Join
                      </button>
                    ) : (
                      <span style={{color:'gray'}}>Full</span>
                    )}
                  </div>
                ))}
              </div>
            )}
            {/* Back button */}
            <div style={{marginTop:'2rem', textAlign:'center'}}>
              <button
                className="btn-secondary"
                onClick={() => setView('teams')}
              >
                Back
              </button>
            </div>
          </div>
        </div>
      )}
      {/* Clubs View */}
      {view === 'clubs' && (
        <div className="auth-wrapper">
          <div className="auth-card auth-card-wide">
            <div className="auth-header">
              <span className="auth-icon">🏟️</span>
              <h2>Clubs</h2>
              <p>Join a club to start playing tennis or padel</p>
            </div>

            {clubsLoading ? (
              <p style={{ color: 'var(--text-muted)', textAlign: 'center' }}>Loading clubs…</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {clubs.map((club: any) => (
                  <div key={club.id} className="feature-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <strong>{club.name}</strong>
                      <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '4px' }}>
                        📍 {club.city} — {club.sports.join(', ')}
                      </p>
                    </div>
                    {userClub === club.id ? (
                      <button className="btn-secondary" onClick={handleLeaveClub} style={{ padding: '8px 20px', fontSize: '0.9rem' }}>
                        Leave
                      </button>
                    ) : (
                      <button className="btn-primary" onClick={() => handleJoinClub(club.id)} disabled={userClub !== null} style={{ padding: '8px 20px', fontSize: '0.9rem' }}>
                        {userClub !== null ? 'Already in a club' : 'Join'}
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
      </div>
    )
  }