import { useState, useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useMessage } from "../hooks/useMessage";
import MessageBanner from "../components/MessageBanner";

export default function ResetPassword() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { message, clearMessage, showMessage } = useMessage();
  const [resetToken, setResetToken] = useState("");
  const [resetPassword, setResetPassword] = useState("");
  const [resetConfirm, setResetConfirm] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const token = searchParams.get("token");
    if (token) setResetToken(token);
  }, [searchParams]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    clearMessage();
    if (resetPassword !== resetConfirm) {
      showMessage("Wachtwoorden komen niet overeen", "error");
      return;
    }
    if (resetPassword.length < 8) {
      showMessage("Wachtwoord moet minimaal 8 tekens bevatten", "error");
      return;
    }
    setLoading(true);
    try {
      const res = await fetch("/api/auth/reset-password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: resetToken, new_password: resetPassword }),
      });
      const data = await res.json();
      if (res.ok) {
        navigate("/login", { state: { message: data.message, type: "success" } });
      } else {
        showMessage(data.error, "error");
      }
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
          <span className="auth-icon">🔒</span>
          <h2>Nieuw wachtwoord instellen</h2>
          <p>Kies een sterk wachtwoord van minimaal 8 tekens.</p>
        </div>
        {resetToken ? (
          <form onSubmit={handleSubmit} className="auth-form">
            <div className="form-group">
              <label>Nieuw wachtwoord</label>
              <input type="password" placeholder="Min. 8 tekens" required value={resetPassword} onChange={(e) => setResetPassword(e.target.value)} />
            </div>
            <div className="form-group">
              <label>Bevestig wachtwoord</label>
              <input type="password" placeholder="Herhaal wachtwoord" required value={resetConfirm} onChange={(e) => setResetConfirm(e.target.value)} />
            </div>
            <button type="submit" className="btn-submit" disabled={loading}>
              {loading ? "Opslaan…" : "Wachtwoord instellen"}
            </button>
          </form>
        ) : (
          <p style={{ textAlign: "center", color: "var(--text-muted)", marginTop: "1rem" }}>
            Geen geldige resetlink gevonden. Vraag een nieuwe aan via "Wachtwoord vergeten".
          </p>
        )}
        <p className="auth-switch">
          <button onClick={() => navigate("/login")}>← Terug naar inloggen</button>
        </p>
      </div>
    </div>
  );
}