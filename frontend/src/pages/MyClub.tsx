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

type ClubLadder = {
  id: number;
  name: string;
  start_date: string;
  end_date: string;
  team_size: number;
  rules: string;
  team_count: number;
};

const STATUS_LABEL: Record<JoinRequest["status"], { label: string; color: string }> = {
  pending:  { label: "In behandeling", color: "#f59e0b" },
  approved: { label: "Goedgekeurd",    color: "#22c55e" },
  rejected: { label: "Afgewezen",      color: "#ef4444" },
};

const TODAY = new Date().toISOString().split("T")[0];

const emptyForm = {
  name: "",
  team_size: "2",
  rules: "",
  start_date: TODAY,
  end_date: "",
};

export default function MyClub() {
  const navigate = useNavigate();
  const { isClubAdmin, myClubName, myClubId, refreshClubStatus } = useAuth();
  const { message, clearMessage, showMessage } = useMessage();

  const [tab, setTab] = useState<"members" | "requests" | "ladders">("ladders");

  // Members
  const [members, setMembers] = useState<Member[]>([]);
  const [membersLoading, setMembersLoading] = useState(false);

  // Join requests
  const [joinRequests, setJoinRequests] = useState<JoinRequest[]>([]);
  const [requestsLoading, setRequestsLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [requestFilter, setRequestFilter] = useState<"pending" | "all">("pending");

  // Ladders
  const [ladders, setLadders] = useState<ClubLadder[]>([]);
  const [laddersLoading, setLaddersLoading] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [creating, setCreating] = useState(false);

  // Delete club
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);

  // Leave club
  const [showLeaveConfirm, setShowLeaveConfirm] = useState(false);
  const [leaveLoading, setLeaveLoading] = useState(false);

  useEffect(() => {
    // Force tab to ladders if the user is not an admin
    if (!isClubAdmin && (tab === "members" || tab === "requests")) {
      setTab("ladders");
    }
  }, [isClubAdmin, tab]);

  useEffect(() => {
    // Redirect to /clubs if the user is entirely clubless
    if (myClubId === null) navigate("/clubs");
  }, [myClubId, navigate]);

  // ── Members ──────────────────────────────────────────────────────────────
  useEffect(() => {
    if (!myClubId || !isClubAdmin) return;
    setMembersLoading(true);
    fetch(`/api/clubs/${myClubId}/members`, {
      headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
    })
      .then((r) => r.json())
      .then((data) => { if (data.success) setMembers(data.members); })
      .catch(() => showMessage("Kon leden niet laden", "error"))
      .finally(() => setMembersLoading(false));
  }, [myClubId, isClubAdmin]);

  // ── Join requests ─────────────────────────────────────────────────────────
  const fetchJoinRequests = () => {
    if (!myClubId || !isClubAdmin) return;
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
    if (tab === "requests" && isClubAdmin) fetchJoinRequests();
  }, [tab, myClubId, isClubAdmin]);

  // ── Ladders ───────────────────────────────────────────────────────────────
  const fetchLadders = () => {
    if (!myClubId) return;
    setLaddersLoading(true);
    fetch(`/api/clubs/${myClubId}/ladders`, {
      headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
    })
      .then((r) => r.json())
      .then((data) => { if (data.success) setLadders(data.ladders); })
      .catch(() => showMessage("Kon ladders niet laden", "error"))
      .finally(() => setLaddersLoading(false));
  };

  useEffect(() => {
    if (tab === "ladders") fetchLadders();
  }, [tab, myClubId]);

  const handleCreateLadder = async () => {
    if (!form.name.trim()) {
      showMessage("Naam is verplicht", "error");
      return;
    }
    if (!form.end_date) {
      showMessage("Einddatum is verplicht", "error");
      return;
    }
    if (form.end_date < form.start_date) {
      showMessage("Einddatum moet na startdatum liggen", "error");
      return;
    }
    setCreating(true);
    try {
      const res = await fetch(`/api/clubs/${myClubId}/ladders`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({
          name: form.name.trim(),
          team_size: parseInt(form.team_size, 10),
          rules: form.rules.trim(),
          start_date: form.start_date,
          end_date: form.end_date,
        }),
      });
      const data = await res.json();
      if (data.success) {
        showMessage("Ladder aangemaakt!", "success");
        setForm(emptyForm);
        setShowCreateForm(false);
        fetchLadders();
      } else {
        showMessage(data.error || "Aanmaken mislukt", "error");
      }
    } catch {
      showMessage("Kan geen verbinding maken met de server", "error");
    } finally {
      setCreating(false);
    }
  };

  // ── Delete club ───────────────────────────────────────────────────────────
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
        await refreshClubStatus();
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

  // ── Leave club ───────────────────────────────────────────────────────────
  const handleLeaveClub = async () => {
    if (!myClubId) return;
    setLeaveLoading(true);
    try {
      const res = await fetch(`/api/clubs/${myClubId}/leave`, {
        method: "POST",
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
      });
      const data = await res.json();
      if (data.success) {
        showMessage("Je hebt de club verlaten", "success");
        await refreshClubStatus();
        navigate("/clubs");
      } else {
        showMessage(data.error || "Kon club niet verlaten", "error");
        setShowLeaveConfirm(false);
      }
    } catch {
      showMessage("Kan geen verbinding maken met de server", "error");
      setShowLeaveConfirm(false);
    } finally {
      setLeaveLoading(false);
    }
  };

  // ── Join request review ───────────────────────────────────────────────────
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

  // ── Tab button helper ─────────────────────────────────────────────────────
  const tabBtn = (value: typeof tab, label: string, badge?: number) => (
    <button
      onClick={() => setTab(value)}
      style={{
        padding: "8px 22px", borderRadius: "20px", border: "1px solid", fontSize: "0.9rem",
        cursor: "pointer", fontFamily: "inherit",
        fontWeight: tab === value ? 600 : 400,
        borderColor: tab === value ? "var(--green-light)" : "var(--border)",
        background: tab === value ? "rgba(64,145,108,0.15)" : "transparent",
        color: tab === value ? "var(--green-light)" : "var(--text-muted)",
        transition: "all 0.15s",
        position: "relative",
      }}
    >
      {label}
      {badge !== undefined && badge > 0 && tab !== value && (
        <span style={{
          marginLeft: "6px", background: "#f59e0b", color: "#000",
          borderRadius: "20px", fontSize: "0.7rem", fontWeight: 700, padding: "1px 7px",
        }}>
          {badge}
        </span>
      )}
    </button>
  );

  return (
    <div className="admin-wrapper">
      <MessageBanner message={message} onClose={clearMessage} />

      <div className="admin-container">
        <div className="admin-header">
          <h1>🏟️ {myClubName ?? "My Club"}</h1>
          <p>{isClubAdmin ? "Beheer je club en leden" : "Bekijk ladders en je club status"}</p>

          {isClubAdmin ? (
            <button
              onClick={() => setShowDeleteConfirm(true)}
              style={{
                marginTop: "0.75rem", padding: "8px 20px", borderRadius: "8px",
                border: "1px solid rgba(239,68,68,0.4)", background: "rgba(239,68,68,0.1)",
                color: "#f87171", cursor: "pointer", fontFamily: "inherit",
                fontWeight: 500, fontSize: "0.9rem",
              }}
            >
              🗑️ Club verwijderen
            </button>
          ) : (
            <button
              onClick={() => setShowLeaveConfirm(true)}
              style={{
                marginTop: "0.75rem", padding: "8px 20px", borderRadius: "8px",
                border: "1px solid rgba(239,68,68,0.4)", background: "rgba(239,68,68,0.1)",
                color: "#f87171", cursor: "pointer", fontFamily: "inherit",
                fontWeight: 500, fontSize: "0.9rem",
              }}
            >
              🚪 Club verlaten
            </button>
          )}
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

        {/* ── LEAVE CONFIRM MODAL ── */}
        {showLeaveConfirm && (
          <div
            style={{
              position: "fixed", inset: 0, zIndex: 400,
              background: "rgba(0,0,0,0.72)", backdropFilter: "blur(6px)",
              display: "flex", alignItems: "center", justifyContent: "center", padding: "1rem",
            }}
            onClick={() => setShowLeaveConfirm(false)}
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
                <div style={{ fontSize: "2.5rem", marginBottom: "0.75rem" }}>🚪</div>
                <h3 style={{ fontSize: "1.2rem", fontFamily: "'Bebas Neue', sans-serif", letterSpacing: "1px", marginBottom: "0.5rem" }}>
                  Club verlaten?
                </h3>
                <p style={{ fontSize: "0.9rem", color: "var(--text-muted)", lineHeight: 1.6 }}>
                  Je staat op het punt om <strong style={{ color: "var(--text)" }}>{myClubName}</strong> te verlaten.
                  Je wordt uit alle actieve ladders en teams van deze club gehaald.
                </p>
              </div>
              <div style={{ display: "flex", gap: "0.75rem" }}>
                <button
                  className="btn-secondary"
                  style={{ flex: 1, padding: "10px" }}
                  disabled={leaveLoading}
                  onClick={() => setShowLeaveConfirm(false)}
                >
                  Annuleren
                </button>
                <button
                  style={{
                    flex: 1, padding: "10px", borderRadius: "8px",
                    border: "1px solid rgba(239,68,68,0.5)", background: "rgba(239,68,68,0.2)",
                    color: "#f87171", cursor: "pointer", fontFamily: "inherit", fontWeight: 600, fontSize: "0.95rem",
                  }}
                  disabled={leaveLoading}
                  onClick={handleLeaveClub}
                >
                  {leaveLoading ? "Bezig…" : "✕ Ja, verlaten"}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ── TAB BAR ── */}
        <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1.5rem", flexWrap: "wrap" }}>
          {isClubAdmin && tabBtn("members",  `👥 Leden (${members.length})`)}
          {isClubAdmin && tabBtn("requests", "📋 Lid-aanvragen", pendingCount)}
          {tabBtn("ladders",  `🏆 Ladders (${ladders.length})`)}
        </div>

        {/* ══════════════════════════════════════════════════════════════════
            TAB: MEMBERS
        ══════════════════════════════════════════════════════════════════ */}
        {tab === "members" && isClubAdmin && (
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

        {/* ══════════════════════════════════════════════════════════════════
            TAB: JOIN REQUESTS
        ══════════════════════════════════════════════════════════════════ */}
        {tab === "requests" && isClubAdmin && (
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
                    <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap", fontSize: "0.82rem", color: "var(--text-muted)" }}>
                      <span>✉️ {req.requester_email}</span>
                      <span>📅 {new Date(req.created_at).toLocaleDateString("nl-BE")}</span>
                    </div>
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
                            padding: "7px 20px", fontSize: "0.88rem", borderRadius: "8px",
                            border: "1px solid rgba(239,68,68,0.4)", background: "rgba(239,68,68,0.1)",
                            color: "#f87171", cursor: "pointer", fontFamily: "inherit", fontWeight: 500,
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

        {/* ══════════════════════════════════════════════════════════════════
            TAB: LADDERS
        ══════════════════════════════════════════════════════════════════ */}
        {tab === "ladders" && (
          <>
            {/* ── Create ladder button / form ── */}
            {isClubAdmin && (
              <div style={{ marginBottom: "1.5rem", display: "flex", justifyContent: "flex-end" }}>
                <button
                  className="btn-primary"
                  style={{ padding: "9px 22px", fontSize: "0.9rem" }}
                  onClick={() => { setShowCreateForm((v) => !v); setForm(emptyForm); }}
                >
                  {showCreateForm ? "✕ Annuleren" : "＋ Nieuwe ladder aanmaken"}
                </button>
              </div>
            )}

            {showCreateForm && (
              <div
                className="admin-card"
                style={{ marginBottom: "1.5rem", padding: "1.75rem 2rem" }}
              >
                <h3 style={{
                  fontFamily: "'Bebas Neue', sans-serif", letterSpacing: "1px",
                  fontSize: "1.4rem", marginBottom: "1.25rem",
                }}>
                  🏆 Nieuwe ladder
                </h3>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
                  {/* Name */}
                  <div className="form-group" style={{ gridColumn: "1 / -1" }}>
                    <label>Naam van de ladder <span style={{ color: "var(--clay)", textTransform: "none" }}>*</span></label>
                    <input
                      type="text"
                      placeholder="bv. Padel Competitie Zomer 2025"
                      value={form.name}
                      onChange={(e) => setForm({ ...form, name: e.target.value })}
                    />
                  </div>

                  {/* Team size */}
                  <div className="form-group">
                    <label>Teamgrootte <span style={{ color: "var(--clay)", textTransform: "none" }}>*</span></label>
                    <select
                      value={form.team_size}
                      onChange={(e) => setForm({ ...form, team_size: e.target.value })}
                      style={{
                        background: "rgba(0,0,0,0.25)", border: "1px solid var(--border)",
                        borderRadius: "8px", color: "var(--text)", fontFamily: "'DM Sans', sans-serif",
                        fontSize: "0.95rem", padding: "11px 14px", outline: "none", width: "100%",
                        cursor: "pointer",
                      }}
                    >
                      <option value="1">1 (solo)</option>
                      <option value="2">2 (duo)</option>
                      <option value="3">3</option>
                      <option value="4">4</option>
                    </select>
                    <span style={{ fontSize: "0.78rem", color: "var(--text-muted)", marginTop: "2px" }}>
                      Aantal spelers per team
                    </span>
                  </div>

                  {/* Start date */}
                  <div className="form-group">
                    <label>Startdatum <span style={{ color: "var(--clay)", textTransform: "none" }}>*</span></label>
                    <input
                      type="date"
                      value={form.start_date}
                      onChange={(e) => setForm({ ...form, start_date: e.target.value })}
                    />
                  </div>

                  {/* End date */}
                  <div className="form-group">
                    <label>Einddatum <span style={{ color: "var(--clay)", textTransform: "none" }}>*</span></label>
                    <input
                      type="date"
                      value={form.end_date}
                      min={form.start_date}
                      onChange={(e) => setForm({ ...form, end_date: e.target.value })}
                    />
                  </div>

                  {/* Rules */}
                  <div className="form-group" style={{ gridColumn: "1 / -1" }}>
                    <label>Regels / uitleg <span style={{ color: "var(--text-muted)", textTransform: "none", fontWeight: 400 }}>(optioneel)</span></label>
                    <textarea
                      rows={4}
                      placeholder="Beschrijf de regels, hoe uitdagingen werken, punten worden berekend, enz."
                      value={form.rules}
                      style={{
                        background: "rgba(0,0,0,0.25)", border: "1px solid var(--border)",
                        borderRadius: "8px", color: "var(--text)", fontFamily: "'DM Sans', sans-serif",
                        fontSize: "0.95rem", padding: "11px 14px", resize: "vertical",
                        minHeight: "100px", outline: "none", transition: "border-color 0.2s", width: "100%",
                      }}
                      onFocus={(e) => { e.currentTarget.style.borderColor = "var(--green-light)"; }}
                      onBlur={(e) => { e.currentTarget.style.borderColor = "var(--border)"; }}
                      onChange={(e) => setForm({ ...form, rules: e.target.value })}
                    />
                  </div>
                </div>

                <div style={{ display: "flex", justifyContent: "flex-end", gap: "0.75rem", marginTop: "1.25rem" }}>
                  <button
                    className="btn-secondary"
                    style={{ padding: "9px 22px", fontSize: "0.9rem" }}
                    disabled={creating}
                    onClick={() => { setShowCreateForm(false); setForm(emptyForm); }}
                  >
                    Annuleren
                  </button>
                  <button
                    className="btn-submit"
                    style={{ padding: "9px 28px", fontSize: "0.9rem", width: "auto", marginTop: 0 }}
                    disabled={creating || !form.name.trim() || !form.end_date}
                    onClick={handleCreateLadder}
                  >
                    {creating ? "Aanmaken…" : "✓ Ladder aanmaken"}
                  </button>
                </div>
              </div>
            )}

            {/* ── Existing ladders ── */}
            <div className="admin-card">
              <div className="admin-card-header">
                <h2>Ladders</h2>
                <p>{ladders.length} ladder{ladders.length !== 1 ? "s" : ""}</p>
              </div>

              {laddersLoading ? (
                <p style={{ padding: "2rem", textAlign: "center", color: "var(--text-muted)" }}>Laden…</p>
              ) : ladders.length === 0 ? (
                <p className="empty-cell" style={{ padding: "2rem" }}>
                  Nog geen ladders. {isClubAdmin && "Maak er één aan via de knop hierboven."}
                </p>
              ) : (
                <div style={{ display: "flex", flexDirection: "column" }}>
                  {ladders.map((ladder, i) => (
                    <div
                      key={ladder.id}
                      style={{
                        padding: "1.25rem 2rem",
                        borderTop: i === 0 ? "none" : "1px solid rgba(255,255,255,0.08)",
                        display: "flex", flexDirection: "column", gap: "0.5rem",
                      }}
                    >
                      {/* Title row */}
                      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", flexWrap: "wrap" }}>
                        <strong style={{ fontSize: "1.05rem" }}>{ladder.name}</strong>
                        <span style={{
                          fontSize: "0.72rem", fontWeight: 600, padding: "2px 9px", borderRadius: "20px",
                          background: "rgba(64,145,108,0.15)", color: "var(--green-light)",
                          border: "1px solid rgba(64,145,108,0.35)",
                        }}>
                          {ladder.team_size === 1 ? "Solo" : `${ladder.team_size} spelers/team`}
                        </span>
                        <span style={{
                          fontSize: "0.72rem", fontWeight: 600, padding: "2px 9px", borderRadius: "20px",
                          background: "rgba(201,119,59,0.15)", color: "var(--clay-light)",
                          border: "1px solid rgba(201,119,59,0.35)",
                        }}>
                          {ladder.team_count} team{ladder.team_count !== 1 ? "s" : ""}
                        </span>
                      </div>

                      {/* Dates */}
                      <div style={{ fontSize: "0.82rem", color: "var(--text-muted)" }}>
                        📅 {new Date(ladder.start_date).toLocaleDateString("nl-BE")}
                        {" – "}
                        {new Date(ladder.end_date).toLocaleDateString("nl-BE")}
                      </div>

                      {/* Rules preview */}
                      {ladder.rules && (
                        <div style={{
                          background: "rgba(255,255,255,0.04)", border: "1px solid var(--border)",
                          borderRadius: "8px", padding: "0.65rem 0.9rem",
                          fontSize: "0.85rem", color: "var(--text)", lineHeight: 1.6,
                          whiteSpace: "pre-wrap",
                        }}>
                          <span style={{
                            fontSize: "0.7rem", color: "var(--text-muted)", display: "block",
                            marginBottom: "3px", textTransform: "uppercase", letterSpacing: "0.4px",
                          }}>
                            Regels
                          </span>
                          {ladder.rules}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}