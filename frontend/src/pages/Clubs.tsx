import { useState, useEffect } from "react";
import { useMessage } from "../hooks/useMessage";
import MessageBanner from "../components/MessageBanner";

type Club = {
  id: number;
  name: string;
  city: string;
  sports: string[];
  request_status: "none" | "pending" | "member";
};

export default function Clubs() {
  const { message, clearMessage, showMessage } = useMessage();
  const [clubs, setClubs] = useState<Club[]>([]);
  const [clubsLoading, setClubsLoading] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchClubs = async () => {
      setClubsLoading(true);
      try {
        const res = await fetch("/api/clubs", {
          headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
        });
        const data = await res.json();
        if (data.success) {
          setClubs(data.clubs);
        }
      } catch (err) {
        console.error("Error fetching clubs:", err);
        showMessage("Could not load clubs", "error");
      } finally {
        setClubsLoading(false);
      }
    };
    fetchClubs();
  }, []);

  const handleRequestJoinClub = async (club_id: number) => {
    setLoading(true);
    clearMessage();
    try {
      const res = await fetch(`/api/clubs/${club_id}/request_join`, {
        method: "POST",
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
      });
      const data = await res.json();
      if (data.success) {
        showMessage("Request to join club sent!", "success");
        setClubs((prev) =>
            prev.map((c) => c.id === club_id ? { ...c, request_status: "pending" } : c)
        );
      } else {
        if (data.error === "club_not_found") showMessage("Club not found", "error");
        else if (data.error === "request_already_exists") showMessage("Request already sent!", "error");
        else showMessage(data.error || "Failed to request join", "error");
      }
    } catch {
      showMessage("Could not connect to server", "error");
    } finally {
      setLoading(false);
    }
  };

  const handleLeaveClub = async (club_id: number) => {
    setLoading(true);
    clearMessage();
    try {
      const res = await fetch(`/api/clubs/${club_id}/leave`, {
        method: "POST",
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
      });
      const data = await res.json();
      if (data.success) {
        showMessage("You have left the club", "success");
        setClubs((prev) =>
            prev.map((c) => c.id === club_id ? { ...c, request_status: "none" } : c)
        );
      } else {
        if (data.error === "club_not_found") showMessage("Club not found", "error");
        else if (data.error === "not_a_member") showMessage("You are not a member of this club", "error");
        else showMessage(data.error || "Failed to leave club", "error");
      }
    } catch {
      showMessage("Could not connect to server", "error");
    } finally {
      setLoading(false);
    }
  }

  const getButtonLabel = (club: Club): string => {
    if (club.request_status === "member") return "Leave";
    if (club.request_status === "pending") return "Request pending";
    return "Join";
  };


  return (
      <div className="auth-wrapper">
        <MessageBanner message={message} onClose={clearMessage} />
        <div className="auth-card auth-card-wide">
          <div className="auth-header">
            <span className="auth-icon">🏟️</span>
            <h2>Clubs</h2>
            <p>Join a club to start playing tennis or padel</p>
          </div>

          {clubsLoading ? (
              <p style={{ color: "var(--text-muted)", textAlign: "center" }}>Loading clubs…</p>
          ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
                {clubs.map((club) => (
                    <div key={club.id} className="feature-card" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <div>
                        <strong>{club.name}</strong>
                        <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", marginTop: "4px" }}>
                          📍 {club.city} — {club.sports.join(", ")}
                        </p>
                      </div>
                      <button
                          className={club.request_status === "member" ? "btn-secondary" : "btn-primary"}
                          style={{padding: "8px 20px", fontSize: "0.9rem"}}
                          disabled={loading || club.request_status === "pending"}
                          onClick={() => {
                            if (club.request_status === "member") {
                                handleLeaveClub(club.id);
                            } else if (club.request_status === "none") {
                              handleRequestJoinClub(club.id);
                            }
                          }}
                      >
                        {getButtonLabel(club)}
                      </button>

                    </div>
                ))}
              </div>
          )}
        </div>
      </div>
  );
}