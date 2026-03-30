import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useMessage } from "../hooks/useMessage";
import MessageBanner from "../components/MessageBanner";

type Team = {
  team_id: number;
  team_name: string;
  member_count: number;
  members: string[];
  ladder_name: string;
  team_size: number;
};

export default function JoinTeams() {
  const navigate = useNavigate();
  const { message, clearMessage, showMessage } = useMessage();
  const [teams, setTeams] = useState<Team[]>([]);
  const [loading, setLoading] = useState(false);
  const [teamsLoading, setTeamsLoading] = useState(false);

  useEffect(() => {
    const fetchTeams = async () => {
      setTeamsLoading(true);
      try {
        const res = await fetch("/api/teams", {
          headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
        });
        const data = await res.json();
        if (data.success) setTeams(data.teams);
      } catch (err) {
        console.error("Error fetching teams:", err);
      } finally {
        setTeamsLoading(false);
      }
    };
    fetchTeams();
  }, []);

  const handleJoinTeam = async (team_id: number) => {
    setLoading(true);
    clearMessage();
    try {
      const res = await fetch(`/api/teams/${team_id}/join`, {
        method: "POST",
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
      });
      const data = await res.json();
      if (!data.success) {
        if (data.error === "already_in_team") showMessage("Already in a team!", "error");
        else if (data.error === "team_full") showMessage("This team is already full", "error");
        else if (data.error === "team_not_found") showMessage("Team not found", "error");
        else showMessage(data.error || "Failed to join team", "error");
      } else {
        showMessage("You joined the team!", "success");
        await fetchTeams();
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
          <span className="auth-icon"></span>
          <h2>Available Teams</h2>
          <p>Join an existing team</p>
        </div>

        {teamsLoading ? (
          <p style={{ color: "var(--text-muted)", textAlign: "center" }}>Loading teams…</p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            {teams.length === 0 && (
              <p style={{ color: "var(--text-muted)", textAlign: "center" }}>No teams available yet</p>
            )}
            {teams.filter(team => team.team_size > 1).map((team) => (
              <div key={team.team_id} className="feature-card" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div>
                  <strong>{team.team_name}</strong>
                  <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", marginTop: "4px" }}>
                    {team.member_count}/2 players — {team.member_count >= 2 ? "Full" : "Open"}
                  </p>
                  <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", margin: "2px 0" }}>
                    Ladder: {team.ladder_name || "No ladder"}
                  </p>
                  <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", margin: "2px 0" }}>
                    Members: {team.members.length > 0 ? team.members.join(" & ") : "No members"}
                  </p>
                </div>
                {team.member_count < team.team_size ? (
                  <button
                    className="btn-primary"
                    onClick={() => handleJoinTeam(team.team_id)}
                    disabled={loading}
                    style={{ padding: "8px 20px", fontSize: "0.9rem" }}
                  >
                    Join
                  </button>
                ) : (
                  <span style={{ color: "gray" }}>Full</span>
                )}
              </div>
            ))}
          </div>
        )}

        <div style={{ marginTop: "2rem", textAlign: "center" }}>
          <button className="btn-secondary" onClick={() => navigate("/teams")}>Back</button>
        </div>
      </div>
    </div>
  );
}