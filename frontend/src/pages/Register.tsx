import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMessage } from "../hooks/useMessage";
import MessageBanner from "../components/MessageBanner";

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
  const { message, clearMessage, showMessage } = useMessage();
  const [loading, setLoading] = useState(false);
  const [registerData, setRegisterData] = useState<User>({
    first_name: "",
    last_name: "",
    email: "",
    date_of_birth: "",
    password: "",
    confirm_password: "",
  });

  const update =
    (field: keyof User) => (e: React.ChangeEvent<HTMLInputElement>) =>
      setRegisterData({ ...registerData, [field]: e.target.value });

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    clearMessage();
    if (registerData.password !== registerData.confirm_password) {
      showMessage("Passwords do not match!", "error");
      return;
    }
    if (registerData.password.length < 8) {
      showMessage("Password must contain at least 8 characters!", "error");
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
        navigate("/login", {
          state: {
            message: "Succesfully made an account! You can now login.",
            type: "success",
          },
        });
      } else {
        if (res.status === 500) return navigate("/500");
        if (res.status === 502 || res.status === 503) return navigate("/502");
        showMessage(data.error || "Registration failed.", "error");
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
      <div className="auth-card auth-card-wide">
        <div className="auth-header">
          <span className="auth-icon">🏅</span>
          <h2>Become a member of your club!</h2>
          <p>Create a profile!</p>
        </div>
        <form onSubmit={handleRegister} className="auth-form">
          <div className="form-row">
            <div className="form-group">
              <label>First name</label>
              <input
                type="text"
                placeholder="John"
                required
                value={registerData.first_name}
                onChange={update("first_name")}
              />
            </div>
            <div className="form-group">
              <label>Last name</label>
              <input
                type="text"
                placeholder="Doe"
                required
                value={registerData.last_name}
                onChange={update("last_name")}
              />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>E-mail</label>
              <input
                type="email"
                placeholder="john.doe@example.com"
                required
                value={registerData.email}
                onChange={update("email")}
              />
            </div>
            <div className="form-group">
              <label>Date of birth</label>
              <input
                type="date"
                required
                value={registerData.date_of_birth}
                onChange={update("date_of_birth")}
              />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label>Password</label>
              <input
                type="password"
                placeholder="Min. 8 characters"
                required
                value={registerData.password}
                onChange={update("password")}
              />
            </div>
            <div className="form-group">
              <label>Confirm password</label>
              <input
                type="password"
                placeholder="Repeat wachtwoord"
                required
                value={registerData.confirm_password}
                onChange={update("confirm_password")}
              />
            </div>
          </div>
          <button type="submit" className="btn-submit" disabled={loading}>
            {loading ? "Creating account…" : "Create account"}
          </button>
        </form>
        <p className="auth-switch">
          Already have an account?{" "}
          <button onClick={() => navigate("/login")}>Log in</button>
        </p>
      </div>
    </div>
  );
}
