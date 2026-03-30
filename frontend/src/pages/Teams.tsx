import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useMessage } from "../hooks/useMessage";
import MessageBanner from "../components/MessageBanner";

interface Team {
  id: string;
  team_name: string;
  ladder_name: string;
  is_solo: boolean;
}

export default function Teams() {
  const navigate = useNavigate();
  const { message, clearMessage, showMessage } = useMessage();
  const [loading, setLoading] = useState(false);
  const [newTeamName, setNewTeamName] = useState("");
  const [userTeams, setUserTeams] = useState<Team[]>([]);
  const [loadingTeams, setLoadingTeams] = useState(true);

  const fetchUserTeams = async () => {
    setLoadingTeams(true);
    try {
      const res = await fetch("/api/teams/my-teams", {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
      });
      const data = await res.json();
      if (data.success) {
        setUserTeams(data.teams);
      } else {
        showMessage(data.error || "Failed to load teams", "error");
      }
    } catch {
      showMessage("Could not connect to server", "error");
    } finally {
      setLoadingTeams(false);
    }
  };

  useEffect(() => {
    fetchUserTeams();
  }, []);

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
        fetchUserTeams();
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
        <div>
          <h3>Your Teams & Solo Entries</h3>
          {loadingTeams ? (
            <p>Loading your teams…</p>
          ) : userTeams.length === 0 ? (
            <p>You are not in any teams or solo ladders yet.</p>
          ) : (
            <ul>
              {userTeams.map((team) => (
                <li key={team.id}>
                  <strong>{team.is_solo ? `Solo: ${team.team_name}` : team.team_name}</strong>
                  {" — "}
                  <em>{team.ladder_name}</em>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}