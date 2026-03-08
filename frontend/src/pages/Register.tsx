import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMessageContext } from "../context/MessageContext";

interface User {
  first_name: string;
  last_name: string;
  email: string;
  date_of_birth: string;
  password: string;
  confirm_password: string;
}

export default function Register() {
  const navigate = useNavigate();
  const { showMessage, clearMessage } = useMessageContext();
  const [loading, setLoading] = useState(false);
  const [registerData, setRegisterData] = useState<User>({
    first_name: "",
    last_name: "",
    email: "",
    date_of_birth: "",
    password: "",
    confirm_password: "",
  });

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    clearMessage();
    if (registerData.password !== registerData.confirm_password) {
      showMessage("Wachtwoorden komen niet overeen", "error");
      return;
    }
    if (registerData.password.length < 8) {
      showMessage("Wachtwoord moet minimaal 8 tekens bevatten", "error");
      return;
    }
    setLoading(true);
    try {
      const res = await fetch("/api/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(registerData),
      });
      const data = await res.json();
      if (res.ok) {
        navigate("/login", { state: { message: "Account aangemaakt! Je kunt nu inloggen." } });
      } else {
        if (res.status === 500) return navigate("/500");
        if (res.status === 502 || res.status === 503) return navigate("/502");
        showMessage(data.error || "Registratie mislukt", "error");
      }
    } catch {
      navigate("/502");
    } finally {
      setLoading(false);
    }
  };

  const update = (field: keyof User) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setRegisterData({ ...registerData, [field]: e.target.value });

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
              <input type="text" placeholder="Jan" required value={registerData.first_name} onChange={update("first_name")} />
            </div>
            <div className="form-group">
              <label>Achternaam</label>
              <input type="text" placeholder="Janssen" required value={registerData.last_name} onChange={update("last_name")} />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>E-mailadres</label>
              <input type="email" placeholder="jan@voorbeeld.com" required value={registerData.email} onChange={update("email")} />
            </div>
            <div className="form-group">
              <label>Geboortedatum</label>
              <input type="date" required value={registerData.date_of_birth} onChange={update("date_of_birth")} />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Wachtwoord</label>
              <input type="password" placeholder="Min. 8 tekens" required value={registerData.password} onChange={update("password")} />
            </div>
            <div className="form-group">
              <label>Bevestig wachtwoord</label>
              <input type="password" placeholder="Herhaal wachtwoord" required value={registerData.confirm_password} onChange={update("confirm_password")} />
            </div>
          </div>
          <button type="submit" className="btn-submit" disabled={loading}>
            {loading ? "Account aanmaken…" : "Account aanmaken"}
          </button>
        </form>
        <p className="auth-switch">
          Al een account?{" "}
          <button onClick={() => { clearMessage(); navigate("/login"); }}>Inloggen</button>
        </p>
      </div>
    </div>
  );
}