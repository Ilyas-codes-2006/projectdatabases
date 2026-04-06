import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useMessage } from "../hooks/useMessage";
import MessageBanner from "../components/MessageBanner";

type MyTeam = {
  team_id: number;
  team_name: string;
  ladder_name: string;
  team_size: number;
  is_solo: boolean;
  member_count: number;
  members: string[];
  elo: number;
};

export default function Teams() {
  const navigate = useNavigate();
  const { message, clearMessage, showMessage } = useMessage();
  const [myTeams, setMyTeams] = useState<MyTeam[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchMyTeams = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/teams/my-teams", {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
      });
      const data = await res.json();
      if (data.success) {
        setMyTeams(data.teams);
      } else {
        showMessage(data.error || "Failed to load teams", "error");
      }
    } catch {
      showMessage("Could not connect to server", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMyTeams();
  }, []);

  // Groepeer per ladder
  const grouped = myTeams.reduce<Record<string, MyTeam[]>>((acc, team) => {
    const key = team.ladder_name || "No ladder";
    if (!acc[key]) acc[key] = [];
    acc[key].push(team);
    return acc;
  }, {});

  return (
    <div className="auth-wrapper">
      <MessageBanner message={message} onClose={clearMessage} />
      <div className="auth-card auth-card-wide">
        <div className="auth-header">
          <span className="auth-icon"></span>
          <h2>My Teams</h2>
          <p>Your current ladder entries</p>
        </div>
        <div style={{ display: "flex", justifyContent: "center", marginBottom: "2rem" }}>
          Not in a team yet?
              Join One!
        </div>
        <div style={{ display: "flex", justifyContent: "center", marginBottom: "2rem" }}>
          <button className="btn-primary" onClick={() => navigate("/teams/join")}>
            Join a Team
          </button>
        </div>
        {loading ? (
          <p style={{ color: "var(--text-muted)", textAlign: "center" }}>Loading your teams…</p>
        ) : myTeams.length === 0 ? (
          <p style={{ color: "var(--text-muted)", textAlign: "center" }}>
            You are not in any teams or solo ladders yet.
          </p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
            {Object.entries(grouped).map(([ladderName, teams]) => (
              <div key={ladderName}>
                <p style={{
                  fontSize: "0.75rem",
                  fontWeight: 700,
                  textTransform: "uppercase",
                  letterSpacing: "0.08em",
                  color: "var(--text-muted)",
                  marginBottom: "0.5rem",
                }}>
                  {ladderName}
                </p>

                <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                  {teams.map((team) => (
                    <div
                      key={team.team_id}
                      className="feature-card"
                      style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}
                    >
                      <div>
                        <strong>{team.team_name}</strong>
                        <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", marginTop: "4px" }}>
                          {team.is_solo
                            ? "Solo entry"
                            : `Members: ${team.members.join(" & ")}`}
                        </p>
                        <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", margin: "2px 0" }}>
                          {team.member_count}/{team.team_size} players · ELO: {team.elo}
                        </p>
                      </div>
                      <span style={{
                        fontSize: "0.78rem",
                        fontWeight: 600,
                        padding: "4px 12px",
                        borderRadius: "999px",
                        background: team.is_solo ? "var(--accent-muted, #e8f4ff)" : "var(--success-muted, #e8fff0)",
                        color: team.is_solo ? "var(--accent, #3b82f6)" : "var(--success, #16a34a)",
                      }}>
                        {team.is_solo ? "Solo" : "Team"}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}