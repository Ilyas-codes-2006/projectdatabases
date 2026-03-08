import { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useMessageContext } from "../context/MessageContext";

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  const { showMessage, clearMessage } = useMessageContext();
  const [loginData, setLoginData] = useState({ email: "", password: "" });
  const [loading, setLoading] = useState(false);

  // Toon berichten die via navigate(..., { state }) zijn meegegeven
  // bv. na registratie of wachtwoord reset
  useEffect(() => {
    const state = location.state as { message?: string } | null;
    if (state?.message) {
      showMessage(state.message, "success");
      // Verwijder state zodat het bericht niet opnieuw verschijnt bij refresh
      window.history.replaceState({}, "");
    }
  }, []);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    clearMessage();
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(loginData),
      });
      const data = await res.json();
      if (res.ok) {
        login(data.token, data.name, data.is_admin);
        showMessage(`Welkom terug, ${data.name}!`, "success");
        navigate("/");
      } else {
        if (res.status === 404) return navigate("/404");
        if (res.status === 500) return navigate("/500");
        if (res.status === 502 || res.status === 503) return navigate("/502");
        showMessage(data.error || "Inloggen mislukt", "error");
      }
    } catch {
      navigate("/502");
    } finally {
      setLoading(false);
    }
  };

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
              onChange={(e) => setLoginData({ ...loginData, email: e.target.value })}
            />
          </div>
          <div className="form-group">
            <label>Wachtwoord</label>
            <input
              type="password"
              placeholder="Jouw wachtwoord"
              required
              value={loginData.password}
              onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
            />
          </div>
          <button type="submit" className="btn-submit" disabled={loading}>
            {loading ? "Inloggen…" : "Inloggen"}
          </button>
        </form>
        <p className="auth-switch">
          <button onClick={() => { clearMessage(); navigate("/forgot-password"); }}>
            Wachtwoord vergeten?
          </button>
        </p>
        <p className="auth-switch">
          Nog geen account?{" "}
          <button onClick={() => { clearMessage(); navigate("/register"); }}>
            Maak er een aan
          </button>
        </p>
      </div>
    </div>
  );
}