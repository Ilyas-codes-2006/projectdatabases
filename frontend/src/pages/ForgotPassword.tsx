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
      showMessage("Could not connect to server.", "error");
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
          <h2>Forgot password</h2>
          <p>
            Fill in your e-mail. If your e-mail has been registeren, we will
            send a mail containing the resetlink.
          </p>
        </div>
        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label>E-mail</label>
            <input
              type="email"
              placeholder="john.doe@example.com"
              required
              value={forgotEmail}
              onChange={(e) => setForgotEmail(e.target.value)}
            />
          </div>
          <button type="submit" className="btn-submit" disabled={loading}>
            {loading ? "Sending…" : "Send resetlink"}
          </button>
        </form>
        <p className="auth-switch">
          <button onClick={() => navigate("/login")}>← Back to log in</button>
        </p>
      </div>
    </div>
  );
}
