import { useEffect, useState } from "react";

interface Team {
  id: number;
  name: string;
  elo: number;
  members: string[];
}

export default function Ladder() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    const fetchLadder = async () => {
      try {
        const token = localStorage.getItem("token");
        const res = await fetch("/api/ladder", {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          const data = await res.json();
          setTeams(data.sort((a: Team, b: Team) => b.elo - a.elo));
        } else {
          setTeams([]);
        }
      } catch (error) {
        console.error("Error fetching ladder:", error);
        setTeams([]);
      } finally {
        setLoading(false);
      }
    };
    fetchLadder();
  }, []);
  //top 5 tonen
  const visibleTeams = expanded ? teams : teams.slice(0, 5);

  return (
    <div className="ladder-container">
      <h2 className="ladder-title">Ladder</h2>

      {loading ? (
        <p className="ladder-empty">Loading...</p>
      ) : teams.length === 0 ? (
        <p className="ladder-empty">No players!</p>
      ) : (
        <>
          <div className="ladder-list">
            {visibleTeams.map((team, index) => (
              <div key={team.id} className="ladder-item">
                <span className="ladder-rank">#{index + 1}</span>
                <span className="ladder-name">
                  {team.name} — {team.members.length > 0 ? team.members.join(" & ") : "No members"}
                </span>
                <span className="ladder-elo">{team.elo}</span>
              </div>
            ))}
          </div>

          {teams.length > 4 && (
            <button
              className="ladder-toggle"
              onClick={() => setExpanded(!expanded)}
            >
              {expanded ? "▲" : "▼"}
            </button>
          )}
        </>
      )}
    </div>
  );
}