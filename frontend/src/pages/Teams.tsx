import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useMessage } from "../hooks/useMessage";
import MessageBanner from "../components/MessageBanner";

export default function Teams() {
  const navigate = useNavigate();
  const { message, clearMessage, showMessage } = useMessage();
  const [loading, setLoading] = useState(false);
  const [newTeamName, setNewTeamName] = useState("");

  const handleCreateTeam = async () => {
    if (!newTeamName) return;
    setLoading(true);
    clearMessage();
    try {
      const res = await fetch("/api/teams", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({ team_name: newTeamName }),
      });
      const data = await res.json();
      if (!data.success) {
        if (data.error === "already_in_team") showMessage("Already in a team!", "error");
        else if (data.error === "no_active_ladder") showMessage("No active ladder found", "error");
        else showMessage(data.error || "Failed to create team", "error");
      } else {
        showMessage("Team created!", "success");
        setNewTeamName("");
      }
    } catch {
      showMessage("Could not connect to server", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-wrapper">
      <MessageBanner message={message} onClose={clearMessage} />
      <div className="auth-card auth-card-wide">
        <div className="auth-header">
          <span className="auth-icon">🏸</span>
          <h2>Padel Teams</h2>
          <p>Create your own team or join another</p>
        </div>

        <div style={{ display: "flex", justifyContent: "center", marginBottom: "2rem" }}>
          <button className="btn-primary" onClick={() => navigate("/teams/join")}>
            Join a Team
          </button>
        </div>

        <div className="auth-form">
          <div className="form-group">
            <label>Create a new team</label>
            <input
              type="text"
              placeholder="Team name…"
              value={newTeamName}
              onChange={(e) => setNewTeamName(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") handleCreateTeam(); }}
            />
          </div>
          <button className="btn-submit" onClick={handleCreateTeam} disabled={loading || !newTeamName}>
            {loading ? "Creating…" : "Create Team"}
          </button>
        </div>
      </div>
    </div>
  );
}