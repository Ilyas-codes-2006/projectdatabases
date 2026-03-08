import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMessage } from "../hooks/useMessage";
import MessageBanner from "../components/MessageBanner";

export default function ForgotPassword() {
  const navigate = useNavigate();
  const { message, clearMessage, showMessage } = useMessage();
  const [forgotEmail, setForgotEmail] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    clearMessage();
    try {
      const res = await fetch("/api/auth/forgot-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: forgotEmail }),
      });
      const data = await res.json();
      showMessage(data.message || data.error, res.ok ? "success" : "error");
      if (res.ok) setForgotEmail("");
    } catch {
      showMessage("Kan geen verbinding maken met de server", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-wrapper">
      <MessageBanner message={message} onClose={clearMessage} />
      <div className="auth-card">
        <div className="auth-header">
          <span className="auth-icon">🔑</span>
          <h2>Wachtwoord vergeten</h2>
          <p>Vul je e-mailadres in. Als het bij ons bekend is, sturen we je een resetlink.</p>
        </div>
        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label>E-mailadres</label>
            <input
              type="email"
              placeholder="jij@voorbeeld.com"
              required
              value={forgotEmail}
              onChange={(e) => setForgotEmail(e.target.value)}
            />
          </div>
          <button type="submit" className="btn-submit" disabled={loading}>
            {loading ? "Versturen…" : "Stuur resetlink"}
          </button>
        </form>
        <p className="auth-switch">
          <button onClick={() => navigate("/login")}>← Terug naar inloggen</button>
        </p>
      </div>
    </div>
  );
}