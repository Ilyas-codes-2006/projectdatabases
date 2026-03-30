import { useEffect, useState } from "react";

interface Team {
  id: number;
  name: string;
  elo: number;
  members: string[];
}

interface LadderData {
  id: number;
  name: string;
  start_date: string;
  end_date: string;
  team_size: number;
  teams: Team[];
}

export default function Ladder() {
  const [ladders, setLadders] = useState<LadderData[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<number[]>([]);
  const [popup, setPopup] = useState<LadderData | null>(null);
  const [teamName, setTeamName] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    fetchLadders();
  }, []);

  const fetchLadders = async () => {
    try {
      const token = localStorage.getItem("token");
      const res = await fetch("/api/ladders", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        console.log("Ladders data:", data); // ← check dit
        setLadders(data);
      }
    } catch (error) {
      console.error("Error fetching ladders:", error);
    } finally {
      setLoading(false);
    }
  };

  const toggle = (id: number) => {
    setExpanded((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const handleJoin = async (ladder: LadderData) => {
      const token = localStorage.getItem("token");

      if (ladder.team_size > 1) {
        setPopup(ladder);
        setTeamName("");
        setMessage("");
      } else {
        try {
          const res = await fetch(`/api/ladders/${ladder.id}/join`, {
            method: "POST",
            headers: { Authorization: `Bearer ${token}` },
          });
          const data = await res.json();

          if (res.ok) {
            setMessage("Joined ladder!");
            fetchLadders(); // refresh the ladder data
          } else {
            setMessage(data.error || "Error joining ladder");
          }
        } catch (error) {
          console.error("Error joining ladder:", error);
          setMessage("Error joining ladder");
        }
      }
    };

  const handleCreateTeam = async () => {
    if (!popup || !teamName.trim()) return;
    const token = localStorage.getItem("token");
    const res = await fetch("/api/teams", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ team_name: teamName, ladder_id: popup.id }),
    });
    const data = await res.json();
    if (res.ok) {
      const ladderId = popup.id;
      setPopup(null);
      setMessage("Team created and joined ladder!");
      await fetchLadders();
      // Expand de ladder zodat de user het team ziet
      setExpanded((prev) =>
        prev.includes(ladderId) ? prev : [...prev, ladderId]
      );
    } else {
      setMessage(data.error || "Error creating team");
    }
  };

  const handleJoinExistingTeam = async (team_id: number) => {
      if (!popup) return;
      const token = localStorage.getItem("token");
      const ladderId = popup.id;

      const res = await fetch(`/api/teams/${team_id}/join`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      const data = await res.json();

      if (data.success) {
        setPopup(null);
        setMessage("Joined team!");
        await fetchLadders();

        // Expand de ladder zodat de gebruiker het team ziet
        setExpanded((prev) =>
          prev.includes(ladderId) ? prev : [...prev, ladderId]
        );
      } else {
        // Toon een nette foutmelding
        setMessage(data.error || "Error joining team");
      }
    };

  return (
    <div className="ladder-container">
      <h2 className="ladder-title">Ladders</h2>

      {message && <p className="ladder-message">{message}</p>}

      {loading ? (
        <p className="ladder-empty">Loading...</p>
      ) : ladders.length === 0 ? (
        <p className="ladder-empty">No ladders found!</p>
      ) : (
        <div className="ladder-list">
          {ladders.map((ladder) => (
            <div key={ladder.id} className="ladder-group">
              <div className="ladder-group-header">
                <span className="ladder-group-name">{ladder.name}</span>
                <div className="ladder-group-right">
                  <button
                    className="ladder-join-btn"
                    onClick={() => handleJoin(ladder)}
                  >
                    Join
                  </button>
                  <button
                    className="ladder-group-toggle"
                    onClick={() => toggle(ladder.id)}
                  >
                    {expanded.includes(ladder.id) ? "▲" : "▼"}
                  </button>
                </div>
              </div>

              {expanded.includes(ladder.id) && (
                <div className="ladder-group-teams">
                  {ladder.teams.length === 0 ? (
                    <p className="ladder-empty">No teams yet!</p>
                  ) : (
                    ladder.teams.map((team, index) => (
                      <div key={team.id} className="ladder-item">
                        <span className="ladder-rank">#{index + 1}</span>
                        <span className="ladder-name">
                          {team.members.length > 1
                            ? `${team.name} — ${team.members.join(" & ")}`
                            : team.name}
                        </span>
                        <span className="ladder-elo">{team.elo}</span>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {popup && (
        <div className="ladder-popup-overlay" onClick={() => setPopup(null)}>
          <div className="ladder-popup" onClick={(e) => e.stopPropagation()}>
            <h3>Join {popup.name}</h3>
            <p className="ladder-popup-sub">
              This ladder requires a team of {popup.team_size}.
            </p>

            <div className="ladder-popup-section">
              <h4>Make a new team</h4>
              <input
                className="ladder-popup-input"
                type="text"
                placeholder="Team name"
                value={teamName}
                onChange={(e) => setTeamName(e.target.value)}
              />
              <button className="ladder-popup-btn" onClick={handleCreateTeam}>
                Create & Join
              </button>
            </div>

            {popup.teams.filter((t) => t.members.length < popup.team_size)
              .length > 0 && (
              <div className="ladder-popup-section">
                <h4>Or join an existing team</h4>
                {popup.teams
                  .filter((t) => t.members.length < popup.team_size)
                  .map((team) => (
                    <div key={team.id} className="ladder-popup-team">
                      <span>
                        {team.members.length > 1
                          ? `${team.name} (${team.members.join(" & ")})`
                          : team.name}
                      </span>
                      <button
                        className="ladder-popup-btn-small"
                        onClick={() => handleJoinExistingTeam(team.id)}
                      >
                        Join
                      </button>
                    </div>
                  ))}
              </div>
            )}

            {message && <p className="ladder-message">{message}</p>}
            <button
              className="ladder-popup-close"
              onClick={() => setPopup(null)}
            >
              ✕ Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}