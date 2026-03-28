import { useEffect, useState } from "react";

interface Team {
  id: number;
  name: string;
  elo: number;
}

export default function Ladder() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchLadder = async () => {
      try {
        const token = localStorage.getItem("token");

        const res = await fetch("/api/ladder", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (res.ok) {
          const data = await res.json();
          const sorted = data.sort((a: Team, b: Team) => b.elo - a.elo);
          setTeams(sorted);
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

  return (
    <div className="ladder-container">
      <h2 className="ladder-title">Ladder</h2>

      {loading ? (
        <p className="ladder-empty">Loading...</p>
      ) : teams.length === 0 ? (
        <p className="ladder-empty">No players!</p>
      ) : (
        <div className="ladder-list">
          {teams.map((team, index) => (
            <div key={team.id} className="ladder-item">
              <span className="ladder-rank">#{index + 1}</span>
              <span className="ladder-name">{team.name}</span>
              <span className="ladder-elo">{team.elo}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}