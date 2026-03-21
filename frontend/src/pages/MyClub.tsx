import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useMessage } from "../hooks/useMessage";
import MessageBanner from "../components/MessageBanner";

type Member = {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  elo: number;
  is_admin: boolean;
};

type JoinRequest = {
  id: number;
  user_id: number;
  requester_name: string;
  requester_email: string;
  motivation: string;
  status: "pending" | "approved" | "rejected";
  created_at: string;
};

const STATUS_LABEL: Record<JoinRequest["status"], { label: string; color: string }> = {
  pending:  { label: "In behandeling", color: "#f59e0b" },
  approved: { label: "Goedgekeurd",    color: "#22c55e" },
  rejected: { label: "Afgewezen",      color: "#ef4444" },
};

export default function MyClub() {
  const navigate = useNavigate();
  const { isClubAdmin, myClubName, myClubId } = useAuth();
  const { message, clearMessage, showMessage } = useMessage();

  const [tab, setTab] = useState<"members" | "requests">("members");
  const [members, setMembers] = useState<Member[]>([]);
  const [membersLoading, setMembersLoading] = useState(false);
  const [joinRequests, setJoinRequests] = useState<JoinRequest[]>([]);
  const [requestsLoading, setRequestsLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [requestFilter, setRequestFilter] = useState<"pending" | "all">("pending");
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);

  useEffect(() => {
    if (!isClubAdmin) navigate("/clubs");
  }, [isClubAdmin, navigate]);

  useEffect(() => {
    if (!myClubId) return;
    setMembersLoading(true);
    fetch(`/api/clubs/${myClubId}/members`, {
      headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
    })
      .then((r) => r.json())
      .then((data) => { if (data.success) setMembers(data.members); })
      .catch(() => showMessage("Kon leden niet laden", "error"))
      .finally(() => setMembersLoading(false));
  }, [myClubId]);

  const fetchJoinRequests = () => {
    if (!myClubId) return;
    setRequestsLoading(true);
    fetch(`/api/clubs/${myClubId}/join-requests`, {
      headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
    })
      .then((r) => r.json())
      .then((data) => { if (data.success) setJoinRequests(data.requests); })
      .catch(() => showMessage("Kon aanvragen niet laden", "error"))
      .finally(() => setRequestsLoading(false));
  };

  useEffect(() => {
    if (tab === "requests") fetchJoinRequests();
  }, [tab, myClubId]);

  const handleDeleteClub = async () => {
    if (!myClubId) return;
    setDeleteLoading(true);
    try {
      const res = await fetch(`/api/clubs/${myClubId}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
      });
      const data = await res.json();
      if (data.success) {
        setShowDeleteConfirm(false);
        navigate("/clubs");
      } else {
        showMessage(data.error || "Verwijderen mislukt", "error");
        setShowDeleteConfirm(false);
      }
    } catch {
      showMessage("Kan geen verbinding maken met de server", "error");
      setShowDeleteConfirm(false);
    } finally {
      setDeleteLoading(false);
    }
  };

  const handleReview = async (id: number, action: "approve" | "reject") => {
    setActionLoading(id);
    try {
      const res = await fetch(`/api/clubs/join-requests/${id}/review`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({ action }),
      });
      const data = await res.json();
      if (data.success) {
        showMessage(
          action === "approve" ? "Lid goedgekeurd!" : "Aanvraag afgewezen.",
          action === "approve" ? "success" : "error"
        );
        const newStatus = action === "approve" ? "approved" : "rejected";
        setJoinRequests((prev) => prev.map((r) => r.id === id ? { ...r, status: newStatus } : r));
        // Refresh members if approved
        if (action === "approve" && myClubId) {
          fetch(`/api/clubs/${myClubId}/members`, {
            headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
          }).then((r) => r.json()).then((d) => { if (d.success) setMembers(d.members); });
        }
      } else {
        showMessage(data.error || "Actie mislukt", "error");
      }
    } catch {
      showMessage("Kan geen verbinding maken met de server", "error");
    } finally {
      setActionLoading(null);
    }
  };

  const pendingCount = joinRequests.filter((r) => r.status === "pending").length;
  const filteredRequests = requestFilter === "pending"
    ? joinRequests.filter((r) => r.status === "pending")
    : joinRequests;

  return (
    <div className="admin-wrapper">
      <MessageBanner message={message} onClose={clearMessage} />
      <div className="admin-container">
        <div className="admin-header">
          <h1>🏟️ {myClubName ?? "My Club"}</h1>
          <p>Beheer je club en leden</p>
          <button
            onClick={() => setShowDeleteConfirm(true)}
            style={{
              marginTop: "0.75rem",
              padding: "8px 20px", borderRadius: "8px", border: "1px solid rgba(239,68,68,0.4)",
              background: "rgba(239,68,68,0.1)", color: "#f87171",
              cursor: "pointer", fontFamily: "inherit", fontWeight: 500, fontSize: "0.9rem",
            }}
          >
            🗑️ Club verwijderen
          </button>
        </div>

        {/* ── DELETE CONFIRM MODAL ── */}
        {showDeleteConfirm && (
          <div
            style={{
              position: "fixed", inset: 0, zIndex: 400,
              background: "rgba(0,0,0,0.72)", backdropFilter: "blur(6px)",
              display: "flex", alignItems: "center", justifyContent: "center", padding: "1rem",
            }}
            onClick={() => setShowDeleteConfirm(false)}
          >
            <div
              style={{
                background: "linear-gradient(160deg, #2d1a1a 0%, #1e1212 100%)",
                border: "1px solid rgba(239,68,68,0.3)",
                borderRadius: "16px", width: "100%", maxWidth: "420px",
                padding: "2rem", boxShadow: "0 24px 60px rgba(0,0,0,0.5)",
                animation: "fadeUp 0.25s ease both",
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <div style={{ textAlign: "center", marginBottom: "1.5rem" }}>
                <div style={{ fontSize: "2.5rem", marginBottom: "0.75rem" }}>⚠️</div>
                <h3 style={{ fontSize: "1.2rem", fontFamily: "'Bebas Neue', sans-serif", letterSpacing: "1px", marginBottom: "0.5rem" }}>
                  Club verwijderen?
                </h3>
                <p style={{ fontSize: "0.9rem", color: "var(--text-muted)", lineHeight: 1.6 }}>
                  Je staat op het punt om <strong style={{ color: "var(--text)" }}>{myClubName}</strong> permanent te verwijderen.
                  Dit kan niet ongedaan worden gemaakt. Alle leden, aanvragen en data gaan verloren.
                </p>
              </div>
              <div style={{ display: "flex", gap: "0.75rem" }}>
                <button
                  className="btn-secondary"
                  style={{ flex: 1, padding: "10px" }}
                  disabled={deleteLoading}
                  onClick={() => setShowDeleteConfirm(false)}
                >
                  Annuleren
                </button>
                <button
                  style={{
                    flex: 1, padding: "10px", borderRadius: "8px",
                    border: "1px solid rgba(239,68,68,0.5)", background: "rgba(239,68,68,0.2)",
                    color: "#f87171", cursor: "pointer", fontFamily: "inherit", fontWeight: 600, fontSize: "0.95rem",
                  }}
                  disabled={deleteLoading}
                  onClick={handleDeleteClub}
                >
                  {deleteLoading ? "Bezig…" : "✕ Ja, verwijderen"}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Tab bar */}
        <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1.5rem" }}>
          <button
            onClick={() => setTab("members")}
            style={{
              padding: "8px 22px", borderRadius: "20px", border: "1px solid", fontSize: "0.9rem",
              cursor: "pointer", fontFamily: "inherit", fontWeight: tab === "members" ? 600 : 400,
              borderColor: tab === "members" ? "var(--green-light)" : "var(--border)",
              background: tab === "members" ? "rgba(64,145,108,0.15)" : "transparent",
              color: tab === "members" ? "var(--green-light)" : "var(--text-muted)",
              transition: "all 0.15s",
            }}
          >
            👥 Leden ({members.length})
          </button>
          <button
            onClick={() => setTab("requests")}
            style={{
              padding: "8px 22px", borderRadius: "20px", border: "1px solid", fontSize: "0.9rem",
              cursor: "pointer", fontFamily: "inherit", fontWeight: tab === "requests" ? 600 : 400,
              borderColor: tab === "requests" ? "var(--green-light)" : "var(--border)",
              background: tab === "requests" ? "rgba(64,145,108,0.15)" : "transparent",
              color: tab === "requests" ? "var(--green-light)" : "var(--text-muted)",
              transition: "all 0.15s",
              position: "relative",
            }}
          >
            📋 Lid-aanvragen
            {pendingCount > 0 && tab !== "requests" && (
              <span style={{
                marginLeft: "6px", background: "#f59e0b", color: "#000",
                borderRadius: "20px", fontSize: "0.7rem", fontWeight: 700, padding: "1px 7px",
              }}>
                {pendingCount}
              </span>
            )}
          </button>
        </div>

        {/* ── MEMBERS TAB ── */}
        {tab === "members" && (
          <div className="admin-card">
            <div className="admin-card-header">
              <h2>Leden</h2>
              <p>{members.length} lid{members.length !== 1 ? "en" : ""}</p>
            </div>
            <div className="admin-table-wrapper">
              {membersLoading ? (
                <p style={{ padding: "1.5rem", textAlign: "center", color: "var(--text-muted)" }}>Laden…</p>
              ) : members.length === 0 ? (
                <p className="empty-cell">Nog geen leden.</p>
              ) : (
                <table className="admin-table">
                  <thead>
                    <tr>
                      <th>Naam</th>
                      <th>E-mail</th>
                      <th>ELO</th>
                      <th>Rol</th>
                    </tr>
                  </thead>
                  <tbody>
                    {members.map((m) => (
                      <tr key={m.id}>
                        <td>{m.first_name} {m.last_name}</td>
                        <td>{m.email}</td>
                        <td>{m.elo}</td>
                        <td>
                          {m.is_admin
                            ? <span style={{ color: "var(--green-light)", fontWeight: 600 }}>Club Admin</span>
                            : <span style={{ color: "var(--text-muted)" }}>Lid</span>
                          }
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        )}

        {/* ── JOIN REQUESTS TAB ── */}
        {tab === "requests" && (
          <div className="admin-card">
            <div className="admin-card-header" style={{ display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: "0.75rem" }}>
              <div>
                <h2>Lid-aanvragen</h2>
                <p>{pendingCount} openstaande aanvra{pendingCount !== 1 ? "gen" : "ag"}</p>
              </div>
              <div style={{ display: "flex", gap: "0.5rem" }}>
                {(["pending", "all"] as const).map((f) => (
                  <button key={f} onClick={() => setRequestFilter(f)} style={{
                    padding: "5px 14px", borderRadius: "20px", border: "1px solid", fontSize: "0.82rem",
                    cursor: "pointer", fontFamily: "inherit",
                    fontWeight: requestFilter === f ? 600 : 400,
                    borderColor: requestFilter === f ? "var(--green-light)" : "var(--border)",
                    background: requestFilter === f ? "rgba(64,145,108,0.15)" : "transparent",
                    color: requestFilter === f ? "var(--green-light)" : "var(--text-muted)",
                  }}>
                    {f === "pending" ? "Openstaand" : "Alle"}
                  </button>
                ))}
              </div>
            </div>

            {requestsLoading ? (
              <p style={{ padding: "2rem", textAlign: "center", color: "var(--text-muted)" }}>Laden…</p>
            ) : filteredRequests.length === 0 ? (
              <p className="empty-cell" style={{ padding: "2rem" }}>
                {requestFilter === "pending" ? "Geen openstaande aanvragen." : "Geen aanvragen gevonden."}
              </p>
            ) : (
              <div style={{ display: "flex", flexDirection: "column" }}>
                {filteredRequests.map((req, i) => (
                  <div key={req.id} style={{
                    padding: "1.25rem 2rem",
                    borderTop: i === 0 ? "none" : "1px solid rgba(255,255,255,0.08)",
                    display: "flex", flexDirection: "column", gap: "0.65rem",
                  }}>
                    {/* Name + status */}
                    <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", flexWrap: "wrap" }}>
                      <strong style={{ fontSize: "1rem" }}>{req.requester_name}</strong>
                      <span style={{
                        fontSize: "0.72rem", fontWeight: 600, padding: "2px 9px", borderRadius: "20px",
                        background: `${STATUS_LABEL[req.status].color}22`,
                        color: STATUS_LABEL[req.status].color,
                        border: `1px solid ${STATUS_LABEL[req.status].color}55`,
                      }}>
                        {STATUS_LABEL[req.status].label}
                      </span>
                    </div>

                    {/* Meta */}
                    <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap", fontSize: "0.82rem", color: "var(--text-muted)" }}>
                      <span>✉️ {req.requester_email}</span>
                      <span>📅 {new Date(req.created_at).toLocaleDateString("nl-BE")}</span>
                    </div>

                    {/* Motivatie */}
                    {req.motivation && (
                      <div style={{
                        background: "rgba(255,255,255,0.04)", border: "1px solid var(--border)",
                        borderRadius: "8px", padding: "0.65rem 0.9rem",
                        fontSize: "0.88rem", color: "var(--text)", lineHeight: 1.6,
                      }}>
                        <span style={{ fontSize: "0.7rem", color: "var(--text-muted)", display: "block", marginBottom: "3px", textTransform: "uppercase", letterSpacing: "0.4px" }}>
                          Motivatie
                        </span>
                        {req.motivation}
                      </div>
                    )}

                    {/* Actions */}
                    {req.status === "pending" && (
                      <div style={{ display: "flex", gap: "0.6rem" }}>
                        <button
                          className="btn-primary"
                          style={{ padding: "7px 20px", fontSize: "0.88rem" }}
                          disabled={actionLoading === req.id}
                          onClick={() => handleReview(req.id, "approve")}
                        >
                          {actionLoading === req.id ? "Bezig…" : "✓ Goedkeuren"}
                        </button>
                        <button
                          style={{
                            padding: "7px 20px", fontSize: "0.88rem",
                            borderRadius: "8px", border: "1px solid rgba(239,68,68,0.4)",
                            background: "rgba(239,68,68,0.1)", color: "#f87171",
                            cursor: "pointer", fontFamily: "inherit", fontWeight: 500,
                          }}
                          disabled={actionLoading === req.id}
                          onClick={() => handleReview(req.id, "reject")}
                          onMouseOver={(e) => (e.currentTarget.style.background = "rgba(239,68,68,0.2)")}
                          onMouseOut={(e) => (e.currentTarget.style.background = "rgba(239,68,68,0.1)")}
                        >
                          ✕ Afwijzen
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}