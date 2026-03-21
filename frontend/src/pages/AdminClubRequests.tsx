import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useMessage } from "../hooks/useMessage";
import MessageBanner from "../components/MessageBanner";

type Attachment = {
  filename: string;
  mimetype: string;
  data_b64: string;
};

type ClubRequest = {
  id: number;
  club_name: string;
  city: string;
  motivation: string;
  status: "pending" | "approved" | "rejected";
  created_at: string;
  requester_name: string;
  requester_email: string;
  attachments_count?: number;
};

type ClubRequestDetail = ClubRequest & {
  attachments: Attachment[];
};

const STATUS_LABEL: Record<ClubRequest["status"], { label: string; color: string }> = {
  pending:  { label: "In behandeling", color: "#f59e0b" },
  approved: { label: "Goedgekeurd",    color: "#22c55e" },
  rejected: { label: "Afgewezen",      color: "#ef4444" },
};

export default function AdminClubRequests() {
  const navigate = useNavigate();
  const { isAdmin } = useAuth();
  const { message, clearMessage, showMessage } = useMessage();
  const [requests, setRequests] = useState<ClubRequest[]>([]);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [filter, setFilter] = useState<"all" | "pending" | "approved" | "rejected">("pending");

  // Detail drawer
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [detail, setDetail] = useState<ClubRequestDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => {
    if (!isAdmin) navigate("/");
  }, [isAdmin, navigate]);

  useEffect(() => {
    const fetchRequests = async () => {
      setLoading(true);
      try {
        const res = await fetch("/api/admin/club-requests", {
          headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
        });
        const data = await res.json();
        if (data.success) setRequests(data.requests);
        else showMessage(data.error || "Kon aanvragen niet laden", "error");
      } catch {
        showMessage("Kan geen verbinding maken met de server", "error");
      } finally {
        setLoading(false);
      }
    };
    fetchRequests();
  }, []);

  const openDetail = async (id: number) => {
    setSelectedId(id);
    setDetail(null);
    setDetailLoading(true);
    try {
      const res = await fetch(`/api/admin/club-requests/${id}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
      });
      const data = await res.json();
      if (data.success) setDetail(data);
      else showMessage(data.error || "Kon detail niet laden", "error");
    } catch {
      showMessage("Kan geen verbinding maken met de server", "error");
    } finally {
      setDetailLoading(false);
    }
  };

  const closeDetail = () => {
    setSelectedId(null);
    setDetail(null);
  };

  const handleReview = async (id: number, action: "approve" | "reject") => {
    setActionLoading(id);
    try {
      const res = await fetch(`/api/admin/club-requests/${id}/review`, {
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
          action === "approve" ? "Club goedgekeurd en aangemaakt!" : "Aanvraag afgewezen.",
          action === "approve" ? "success" : "error"
        );
        const newStatus = action === "approve" ? "approved" : "rejected";
        setRequests((prev) => prev.map((r) => r.id === id ? { ...r, status: newStatus } : r));
        if (detail && detail.id === id) setDetail({ ...detail, status: newStatus });
      } else {
        showMessage(data.error || "Actie mislukt", "error");
      }
    } catch {
      showMessage("Kan geen verbinding maken met de server", "error");
    } finally {
      setActionLoading(null);
    }
  };

  const downloadAttachment = (att: Attachment) => {
    const bytes = atob(att.data_b64);
    const arr = new Uint8Array(bytes.length);
    for (let i = 0; i < bytes.length; i++) arr[i] = bytes.charCodeAt(i);
    const blob = new Blob([arr], { type: att.mimetype });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = att.filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const isImage = (mime: string) => mime.startsWith("image/");

  const filtered = filter === "all" ? requests : requests.filter((r) => r.status === filter);
  const pendingCount = requests.filter((r) => r.status === "pending").length;

  return (
    <div className="admin-wrapper" style={{ position: "relative" }}>
      <MessageBanner message={message} onClose={clearMessage} />
      <div className="admin-container">

        <div style={{ display: "flex", alignItems: "center", gap: "1rem", marginBottom: "1.5rem" }}>
          <button className="btn-secondary" style={{ padding: "8px 16px", fontSize: "0.85rem" }} onClick={() => navigate("/admin")}>
            ← Terug naar Admin
          </button>
        </div>

        <div className="admin-header">
          <h1>🏗️ Club-aanvragen</h1>
          <p>Bekijk en beoordeel ingediende clubaanvragen</p>
        </div>

        {/* Filter tabs */}
        <div style={{ display: "flex", gap: "0.5rem", marginBottom: "1.5rem", flexWrap: "wrap" }}>
          {(["pending", "all", "approved", "rejected"] as const).map((f) => (
            <button key={f} onClick={() => setFilter(f)} style={{
              padding: "6px 16px", borderRadius: "20px", border: "1px solid", fontSize: "0.85rem",
              cursor: "pointer", fontFamily: "inherit",
              fontWeight: filter === f ? 600 : 400,
              borderColor: filter === f ? "var(--green-light)" : "var(--border)",
              background: filter === f ? "rgba(64,145,108,0.15)" : "transparent",
              color: filter === f ? "var(--green-light)" : "var(--text-muted)",
              transition: "all 0.15s",
            }}>
              {f === "pending" && `In behandeling${pendingCount > 0 ? ` (${pendingCount})` : ""}`}
              {f === "all" && "Alle"}
              {f === "approved" && "Goedgekeurd"}
              {f === "rejected" && "Afgewezen"}
            </button>
          ))}
        </div>

        <div className="admin-card">
          <div className="admin-card-header">
            <h2>Aanvragen</h2>
            <p>{filtered.length} aanvra{filtered.length !== 1 ? "gen" : "ag"}</p>
          </div>

          {loading ? (
            <p style={{ padding: "2rem", textAlign: "center", color: "var(--text-muted)" }}>Laden…</p>
          ) : filtered.length === 0 ? (
            <p className="empty-cell" style={{ padding: "2rem" }}>
              {filter === "pending" ? "Geen openstaande aanvragen." : "Geen aanvragen gevonden."}
            </p>
          ) : (
            <div style={{ display: "flex", flexDirection: "column" }}>
              {filtered.map((req, i) => (
                <div
                  key={req.id}
                  style={{
                    padding: "1.25rem 2rem",
                    borderTop: i === 0 ? "none" : "1px solid rgba(255,255,255,0.08)",
                    display: "flex", alignItems: "center", gap: "1rem",
                    cursor: "pointer", transition: "background 0.15s",
                    background: selectedId === req.id ? "rgba(64,145,108,0.08)" : "transparent",
                  }}
                  onClick={() => selectedId === req.id ? closeDetail() : openDetail(req.id)}
                  onMouseOver={(e) => { if (selectedId !== req.id) e.currentTarget.style.background = "rgba(255,255,255,0.03)"; }}
                  onMouseOut={(e) => { if (selectedId !== req.id) e.currentTarget.style.background = "transparent"; }}
                >
                  {/* Left: info */}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", flexWrap: "wrap", marginBottom: "4px" }}>
                      <strong style={{ fontSize: "1rem" }}>{req.club_name}</strong>
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
                      <span>📍 {req.city}</span>
                      <span>👤 {req.requester_name}</span>
                      <span>📅 {new Date(req.created_at).toLocaleDateString("nl-BE")}</span>
                      {!!req.attachments_count && <span>📎 {req.attachments_count}</span>}
                    </div>
                  </div>
                  {/* Right: chevron */}
                  <span style={{
                    color: "var(--text-muted)", fontSize: "0.9rem", flexShrink: 0,
                    transform: selectedId === req.id ? "rotate(90deg)" : "none",
                    transition: "transform 0.2s",
                  }}>›</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* ── DETAIL DRAWER ── */}
      {selectedId !== null && (
        <div
          style={{
            position: "fixed", inset: 0, zIndex: 300,
            background: "rgba(0,0,0,0.6)", backdropFilter: "blur(4px)",
          }}
          onClick={closeDetail}
        >
          <div
            style={{
              position: "absolute", top: 0, right: 0, bottom: 0,
              width: "100%", maxWidth: "540px",
              background: "linear-gradient(160deg, #1a3526 0%, #132418 100%)",
              borderLeft: "1px solid rgba(64,145,108,0.25)",
              overflowY: "auto",
              boxShadow: "-20px 0 60px rgba(0,0,0,0.5)",
              animation: "slideInRight 0.25s ease both",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Drawer header */}
            <div style={{
              padding: "1.5rem 1.75rem",
              borderBottom: "1px solid rgba(255,255,255,0.08)",
              display: "flex", alignItems: "center", justifyContent: "space-between", gap: "1rem",
            }}>
              <h2 style={{ fontSize: "1.15rem", fontFamily: "'Bebas Neue', sans-serif", letterSpacing: "1px" }}>
                Aanvraag detail
              </h2>
              <button onClick={closeDetail} style={{
                background: "rgba(255,255,255,0.07)", border: "1px solid rgba(255,255,255,0.1)",
                borderRadius: "8px", color: "var(--text-muted)", cursor: "pointer",
                fontSize: "1rem", padding: "4px 10px", fontFamily: "inherit",
              }}>✕</button>
            </div>

            {detailLoading ? (
              <p style={{ padding: "2rem", textAlign: "center", color: "var(--text-muted)" }}>Laden…</p>
            ) : detail ? (
              <div style={{ padding: "1.5rem 1.75rem", display: "flex", flexDirection: "column", gap: "1.25rem" }}>

                {/* Status badge */}
                <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                  <strong style={{ fontSize: "1.3rem" }}>{detail.club_name}</strong>
                  <span style={{
                    fontSize: "0.75rem", fontWeight: 600, padding: "3px 12px", borderRadius: "20px",
                    background: `${STATUS_LABEL[detail.status].color}22`,
                    color: STATUS_LABEL[detail.status].color,
                    border: `1px solid ${STATUS_LABEL[detail.status].color}55`,
                  }}>
                    {STATUS_LABEL[detail.status].label}
                  </span>
                </div>

                {/* Info grid */}
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem" }}>
                  {[
                    { label: "Stad", value: detail.city },
                    { label: "Datum", value: new Date(detail.created_at).toLocaleDateString("nl-BE") },
                    { label: "Aanvrager", value: detail.requester_name },
                    { label: "E-mail", value: detail.requester_email },
                  ].map(({ label, value }) => (
                    <div key={label} style={{
                      background: "rgba(255,255,255,0.04)", border: "1px solid var(--border)",
                      borderRadius: "8px", padding: "0.65rem 0.9rem",
                    }}>
                      <p style={{ fontSize: "0.7rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: "2px" }}>{label}</p>
                      <p style={{ fontSize: "0.88rem", wordBreak: "break-word" }}>{value}</p>
                    </div>
                  ))}
                </div>

                {/* Motivatie */}
                {detail.motivation && (
                  <div style={{
                    background: "rgba(255,255,255,0.04)", border: "1px solid var(--border)",
                    borderRadius: "8px", padding: "0.9rem 1rem",
                  }}>
                    <p style={{ fontSize: "0.7rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: "6px" }}>Motivatie</p>
                    <p style={{ fontSize: "0.9rem", lineHeight: 1.65 }}>{detail.motivation}</p>
                  </div>
                )}

                {/* Bijlagen */}
                {detail.attachments.length > 0 && (
                  <div>
                    <p style={{ fontSize: "0.7rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: "0.6rem" }}>
                      Bijlagen ({detail.attachments.length})
                    </p>
                    <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
                      {detail.attachments.map((att, i) => (
                        <div key={i} style={{
                          background: "rgba(255,255,255,0.04)", border: "1px solid var(--border)",
                          borderRadius: "10px", overflow: "hidden",
                        }}>
                          {/* Image preview */}
                          {isImage(att.mimetype) && (
                            <img
                              src={`data:${att.mimetype};base64,${att.data_b64}`}
                              alt={att.filename}
                              style={{ width: "100%", maxHeight: "220px", objectFit: "contain", background: "rgba(0,0,0,0.3)", display: "block" }}
                            />
                          )}
                          {/* File row */}
                          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", padding: "0.6rem 0.9rem" }}>
                            <span style={{ fontSize: "1.3rem" }}>
                              {isImage(att.mimetype) ? "🖼️" : att.mimetype === "application/pdf" ? "📄" : "📎"}
                            </span>
                            <span style={{ flex: 1, fontSize: "0.85rem", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                              {att.filename}
                            </span>
                            <button
                              onClick={() => downloadAttachment(att)}
                              style={{
                                background: "rgba(64,145,108,0.15)", border: "1px solid rgba(64,145,108,0.3)",
                                borderRadius: "6px", color: "var(--green-light)", cursor: "pointer",
                                fontSize: "0.8rem", padding: "4px 10px", fontFamily: "inherit", flexShrink: 0,
                              }}
                            >
                              ↓ Download
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Actieknoppen */}
                {detail.status === "pending" && (
                  <div style={{ display: "flex", gap: "0.75rem", paddingTop: "0.5rem" }}>
                    <button
                      className="btn-primary"
                      style={{ flex: 1, padding: "10px" }}
                      disabled={actionLoading === detail.id}
                      onClick={() => handleReview(detail.id, "approve")}
                    >
                      {actionLoading === detail.id ? "Bezig…" : "✓ Goedkeuren"}
                    </button>
                    <button
                      style={{
                        flex: 1, padding: "10px", borderRadius: "8px",
                        border: "1px solid rgba(239,68,68,0.4)", background: "rgba(239,68,68,0.1)",
                        color: "#f87171", cursor: "pointer", fontFamily: "inherit", fontWeight: 500,
                      }}
                      disabled={actionLoading === detail.id}
                      onClick={() => handleReview(detail.id, "reject")}
                    >
                      ✕ Afwijzen
                    </button>
                  </div>
                )}
              </div>
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
}