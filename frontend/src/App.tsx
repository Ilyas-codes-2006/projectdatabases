import { useState } from 'react'
import { Routes, Route, useNavigate, useLocation, Navigate } from 'react-router-dom'
import './App.css'

import HomePage from './pages/HomePage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage.tsx'
import ForgotPasswordPage from './pages/ForgotPasswordPage'
import ResetPasswordPage from './pages/ResetPasswordPage.tsx'
import AdminPage from './pages/AdminPage.tsx'
import NotFound from './pages/notfound'
import ServerError from './pages/servererror'
import BadGateway from './pages/badgateway'

export default function App() {
  const navigate = useNavigate()
  const location = useLocation()

  const [message, setMessage] = useState<{ text: string; type: 'error' | 'success' } | null>(null)

  const [loggedInUser, setLoggedInUser] = useState<string | null>(() =>
    localStorage.getItem('userName')
  )

  const [isAdmin, setIsAdmin] = useState<boolean>(() =>
    localStorage.getItem('is_admin') === 'true'
  )

  const clearMessage = () => setMessage(null)

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('userName')
    localStorage.removeItem('is_admin')
    setLoggedInUser(null)
    setIsAdmin(false)
    setMessage({ text: 'Je bent uitgelogd.', type: 'success' })
    navigate('/')
  }

  const handleLoginSuccess = (name: string, token: string, is_admin: boolean) => {
    localStorage.setItem('token', token)
    localStorage.setItem('userName', name)
    localStorage.setItem('is_admin', String(is_admin))
    setLoggedInUser(name)
    setIsAdmin(is_admin)
    setMessage({ text: `Welkom terug, ${name}!`, type: 'success' })
    navigate('/')
  }

  const handleRegisterSuccess = () => {
    setMessage({ text: 'Account aangemaakt! Je kunt nu inloggen.', type: 'success' })
    navigate('/login')
  }

  return (
    <div className="app">
      {/* ------------------------------------------------------------------ */}
      {/* Navbar                                                              */}
      {/* ------------------------------------------------------------------ */}
      <nav className="navbar">
        <div className="nav-brand" onClick={() => navigate('/')}>
          <span className="nav-logo">🎾</span>
          <span className="nav-title">MatchUp</span>
        </div>
        <div className="nav-links">
          <button
            className={`nav-btn ${location.pathname === '/' ? 'active' : ''}`}
            onClick={() => navigate('/')}
          >
            Home
          </button>
          {!loggedInUser ? (
            <>
              <button
                className={`nav-btn ${location.pathname === '/login' ? 'active' : ''}`}
                onClick={() => { clearMessage(); navigate('/login') }}
              >
                Login
              </button>
              <button
                className="nav-btn nav-cta"
                onClick={() => { clearMessage(); navigate('/register') }}
              >
                Join Now
              </button>
            </>
          ) : (
            <>
              {isAdmin && (
                <button
                  className={`nav-btn ${location.pathname === '/admin' ? 'active' : ''}`}
                  onClick={() => { clearMessage(); navigate('/admin') }}
                >
                  Admin
                </button>
              )}
              <span className="nav-user">👋 {loggedInUser}</span>
              <button className="nav-btn" onClick={handleLogout}>Logout</button>
            </>
          )}
        </div>
      </nav>

      {/* ------------------------------------------------------------------ */}
      {/* Message Banner                                                      */}
      {/* ------------------------------------------------------------------ */}
      {message && (
        <div className={`message-banner ${message.type}`} onClick={clearMessage}>
          {message.text} <span className="message-close">×</span>
        </div>
      )}

      {/* ------------------------------------------------------------------ */}
      {/* Routes                                                              */}
      {/* ------------------------------------------------------------------ */}
      <Routes>
        <Route
          path="/"
          element={
            <HomePage
              loggedInUser={loggedInUser}
              onNavigate={(path) => { clearMessage(); navigate(path) }}
            />
          }
        />

        <Route
          path="/login"
          element={
            loggedInUser
              ? <Navigate to="/" replace />
              : <LoginPage
                  onSuccess={handleLoginSuccess}
                  onNavigate={(path) => { clearMessage(); navigate(path) }}
                  setMessage={setMessage}
                />
          }
        />

        <Route
          path="/register"
          element={
            loggedInUser
              ? <Navigate to="/" replace />
              : <RegisterPage
                  onSuccess={handleRegisterSuccess}
                  onNavigate={(path) => { clearMessage(); navigate(path) }}
                  setMessage={setMessage}
                />
          }
        />

        <Route
          path="/forgot-password"
          element={
            <ForgotPasswordPage
              onNavigate={(path) => { clearMessage(); navigate(path) }}
              setMessage={setMessage}
            />
          }
        />

        <Route
          path="/reset-password"
          element={
            <ResetPasswordPage
              onNavigate={(path) => { clearMessage(); navigate(path) }}
              setMessage={setMessage}
            />
          }
        />

        <Route
          path="/admin"
          element={
            loggedInUser && isAdmin
              ? <AdminPage setMessage={setMessage} />
              : <Navigate to="/" replace />
          }
        />

        <Route path="/500" element={<ServerError />} />
        <Route path="/502" element={<BadGateway />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </div>
  )
}