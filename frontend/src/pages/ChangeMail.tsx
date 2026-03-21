import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function ChangeEmail() {
  const { loggedInUser } = useAuth();
  const navigate = useNavigate();

  const [newEmail, setNewEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState("");

  if (!loggedInUser) {
    navigate("/login");
    return null;
  }

  const handleChangeEmail = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (!newEmail || !password || !confirmPassword) {
      setError("All fields are required.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setSaving(true);

    try {
      const res = await fetch("/api/profile/change-email", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({
          new_email: newEmail,
          password,
        }),
      });

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.error || "Failed to update email");
      }

      setSuccess("Email successfully updated!");
      setTimeout(() => navigate("/profile"), 1500);
    } catch (err: any) {
      setError(err.message || "Something went wrong.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="profile-wrapper">
      <div className="profile-card" style={{ maxWidth: "400px" }}>
        <h2 className="profile-section-title"
            style={{
            textAlign: "center",
            fontSize: "1.8rem",
            marginTop: "0",
            marginBottom: "1.5rem"
          }}
        >
          Change Email
        </h2>

        <form className="auth-form" onSubmit={handleChangeEmail}>
          <div className="form-group">
            <label htmlFor="new-email">New Email</label>
            <input
              type="email"
              id="new-email"
              value={newEmail}
              onChange={(e) => setNewEmail(e.target.value)}
              placeholder="newemail@example.com"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Current Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your current password"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="confirm-password">Confirm Password</label>
            <input
              type="password"
              id="confirm-password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Confirm your password"
              required
            />
          </div>

          {error && <p className="profile-error">{error}</p>}
          {success && <p style={{ color: "var(--green-light)", textAlign: "center" }}>{success}</p>}

          <button type="submit" className="btn-submit" disabled={saving}>
            {saving ? "Saving…" : "Update Email"}
          </button>

          <button
            type="button"
            className="btn-secondary"
            onClick={() => navigate("/profile")}
            style={{ marginTop: "0.5rem" }}
          >
            Cancel
          </button>
        </form>
      </div>
    </div>
  );
}