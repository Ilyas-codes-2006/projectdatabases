import { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useMessage } from "../hooks/useMessage";
import MessageBanner from "../components/MessageBanner";

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  const { message, clearMessage, showMessage } = useMessage();
  const [loginData, setLoginData] = useState({ email: "", password: "" });
  const [loading, setLoading] = useState(false);

  // Show messages passed via navigate state (e.g. "Account aangemaakt!", "Wachtwoord gewijzigd")
  useEffect(() => {
    if (location.state?.message) {
      showMessage(location.state.message, location.state.type ?? "success");
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
        navigate("/", {
          state: { message: `Welcome back, ${data.name}!`, type: "success" },
        });
      } else {
        if (res.status === 404) return navigate("/404");
        if (res.status === 500) return navigate("/500");
        if (res.status === 502 || res.status === 503) return navigate("/502");
        showMessage(data.error || "Logging in failed!", "error");
      }
    } catch {
      navigate("/502");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-wrapper">
      <MessageBanner message={message} onClose={clearMessage} />
      <div className="auth-card">
        <div className="auth-header">
          <span className="auth-icon">🎾</span>
          <h2>Welcome back!</h2>
          <p>Log in to your account</p>
        </div>
        <form onSubmit={handleLogin} className="auth-form">
          <div className="form-group">
            <label htmlFor="login-email">E-mail</label>
            <input
              id="login-email"
              type="email"
              placeholder="john.doe@example.com"
              required
              value={loginData.email}
              onChange={(e) =>
                setLoginData({ ...loginData, email: e.target.value })
              }
            />
          </div>
          <div className="form-group">
            <label htmlFor="login-password">Password</label>
            <input
              id="login-password"
              type="password"
              placeholder="Your password"
              required
              value={loginData.password}
              onChange={(e) =>
                setLoginData({ ...loginData, password: e.target.value })
              }
            />
          </div>
          <button type="submit" className="btn-submit" disabled={loading}>
            {loading ? "Logging in…" : "Log in"}
          </button>
        </form>
        <p className="auth-switch">
          <button onClick={() => navigate("/forgot-password")}>
            Forgot password?
          </button>
        </p>
        <p className="auth-switch">
          Don't have an account?{" "}
          <button onClick={() => navigate("/register")}>Create one here</button>
        </p>
      </div>
    </div>
  );
}
