import { useState, useEffect, useRef } from "react";
import { useMessage } from "../hooks/useMessage";
import MessageBanner from "../components/MessageBanner";
import { useAuth } from "../context/AuthContext";

type Club = {
  id: number;
  name: string;
  city: string;
  sports: string[];
  has_pending_request: boolean;
  request_status: "none" | "pending" | "member";
};

type AttachedFile = {
  file: File;
  preview?: string;
};

export default function Clubs() {
  const { message, clearMessage, showMessage } = useMessage();
  const { isClubAdmin } = useAuth();
  const [clubs, setClubs] = useState<Club[]>([]);
  const [clubsLoading, setClubsLoading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [userClub, setUserClub] = useState<number | null>(null);

  // New club request modal
  const [showModal, setShowModal] = useState(false);
  const [requestLoading, setRequestLoading] = useState(false);
  const [form, setForm] = useState({ club_name: "", city: "", motivation: "" });
  const [attachedFiles, setAttachedFiles] = useState<AttachedFile[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Join request modal
  const [joinTarget, setJoinTarget] = useState<Club | null>(null);
  const [joinMotivation, setJoinMotivation] = useState("");
  const [joinLoading, setJoinLoading] = useState(false);

  const MAX_FILES = 5;
  const MAX_SIZE_MB = 5;

  const addFiles = (incoming: FileList | File[]) => {
    const arr = Array.from(incoming);
    const valid: AttachedFile[] = [];
    for (const f of arr) {
      if (attachedFiles.length + valid.length >= MAX_FILES) {
        showMessage(`Maximum ${MAX_FILES} bestanden toegestaan`, "error");
        break;
      }
      if (f.size > MAX_SIZE_MB * 1024 * 1024) {
        showMessage(`"${f.name}" is te groot (max ${MAX_SIZE_MB} MB)`, "error");
        continue;
      }
      const preview = f.type.startsWith("image/") ? URL.createObjectURL(f) : undefined;
      valid.push({ file: f, preview });
    }
    setAttachedFiles((prev) => [...prev, ...valid]);
  };

  const removeFile = (idx: number) => {
    setAttachedFiles((prev) => {
      const copy = [...prev];
      if (copy[idx].preview) URL.revokeObjectURL(copy[idx].preview!);
      copy.splice(idx, 1);
      return copy;
    });
  };

  const closeModal = () => {
    setShowModal(false);
    setForm({ club_name: "", city: "", motivation: "" });
    attachedFiles.forEach((f) => { if (f.preview) URL.revokeObjectURL(f.preview); });
    setAttachedFiles([]);
  };

  const handleRequestClub = async () => {
    if (!form.club_name.trim() || !form.city.trim()) {
      showMessage("Clubnaam en stad zijn verplicht", "error");
      return;
    }
    setRequestLoading(true);
    clearMessage();
    try {
      const fd = new FormData();
      fd.append("club_name", form.club_name.trim());
      fd.append("city", form.city.trim());
      fd.append("motivation", form.motivation.trim());
      attachedFiles.forEach(({ file }) => fd.append("attachments", file));

      const res = await fetch("/api/clubs/request", {
        method: "POST",
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
        body: fd,
      });
      const data = await res.json();
      if (data.success) {
        showMessage("Aanvraag ingediend! Een admin wordt per e-mail op de hoogte gebracht.", "success");
        closeModal();
      } else {
        showMessage(data.error || "Aanvraag mislukt", "error");
      }
    } catch {
      showMessage("Kon geen verbinding maken met de server", "error");
    } finally {
      setRequestLoading(false);
    }
  };

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
          setUserClub(data.user_club ?? null);
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

  const handleSubmitJoinRequest = async () => {
    if (!joinTarget) return;
    setJoinLoading(true);
    clearMessage();
    try {
      const res = await fetch(`/api/clubs/${joinTarget.id}/join-request`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({ motivation: joinMotivation }),
      });
      const data = await res.json();
      if (data.success) {
        showMessage(`Aanvraag verstuurd naar de club admin van ${joinTarget.name}!`, "success");
        setClubs((prev) =>
          prev.map((c) =>
            c.id === joinTarget.id
              ? { ...c, has_pending_request: true, request_status: "pending" }
              : c
          )
        );
        setJoinTarget(null);
        setJoinMotivation("");
      } else {
        const errMap: Record<string, string> = {
          already_member: "Je bent al lid van deze club.",
          request_already_pending: "Je hebt al een openstaande aanvraag voor deze club.",
          club_not_found: "Club niet gevonden.",
        };
        showMessage(errMap[data.error] || data.error || "Aanvraag mislukt", "error");
      }
    } catch {
      showMessage("Kon geen verbinding maken met de server", "error");
    } finally {
      setJoinLoading(false);
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
          prev.map((c) =>
            c.id === club_id ? { ...c, request_status: "none" } : c
          )
        );
        setUserClub(null);
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
  };

  const fileIcon = (name: string) => {
    const ext = name.split(".").pop()?.toLowerCase();
    if (["jpg", "jpeg", "png", "gif", "webp", "svg"].includes(ext ?? "")) return "🖼️";
    if (["pdf"].includes(ext ?? "")) return "📄";
    if (["doc", "docx"].includes(ext ?? "")) return "📝";
    return "📎";
  };

  const formatBytes = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
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

        {!isClubAdmin && (
          <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: "1rem" }}>
            <button
              className="btn-secondary"
              style={{ padding: "8px 20px", fontSize: "0.9rem", display: "flex", alignItems: "center", gap: "6px" }}
              onClick={() => setShowModal(true)}
            >
              <span>➕</span> Nieuwe club aanvragen
            </button>
          </div>
        )}

        {clubsLoading ? (
          <p style={{ color: "var(--text-muted)", textAlign: "center" }}>Loading clubs…</p>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
            {clubs.map((club) => {
              const isMember = club.request_status === "member";
              const isPending = club.request_status === "pending" || club.has_pending_request;
              const inOtherClub = userClub !== null && !isMember;

              return (
                <div key={club.id} className="feature-card" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div>
                    <strong>{club.name}</strong>
                    <p style={{ color: "var(--text-muted)", fontSize: "0.85rem", marginTop: "4px" }}>
                      📍 {club.city} — {club.sports.join(", ")}
                    </p>
                  </div>

                  {isMember ? (
                    <button
                      className="btn-secondary"
                      style={{ padding: "8px 20px", fontSize: "0.9rem" }}
                      disabled={loading}
                      onClick={() => handleLeaveClub(club.id)}
                    >
                      Leave
                    </button>
                  ) : isPending ? (
                    <span style={{
                      fontSize: "0.8rem", fontWeight: 600, padding: "5px 14px", borderRadius: "20px",
                      background: "rgba(245,158,11,0.12)", color: "#f59e0b",
                      border: "1px solid rgba(245,158,11,0.3)",
                    }}>⏳ Aanvraag ingediend</span>
                  ) : isClubAdmin ? (
                    <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>Je beheert al een club</span>
                  ) : inOtherClub ? (
                    <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>Al lid van andere club</span>
                  ) : (
                    <button
                      className="btn-primary"
                      style={{ padding: "8px 20px", fontSize: "0.9rem" }}
                      onClick={() => setJoinTarget(club)}
                    >
                      Aanvragen
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* ── NEW CLUB MODAL ── */}
      {showModal && (
        <div
          style={{
            position: "fixed", inset: 0, zIndex: 200,
            background: "rgba(0,0,0,0.72)", backdropFilter: "blur(6px)",
            display: "flex", alignItems: "center", justifyContent: "center", padding: "1rem",
          }}
          onClick={(e) => { if (e.target === e.currentTarget) closeModal(); }}
        >
          <div
            style={{
              background: "linear-gradient(160deg, #1e3d2c 0%, #162e22 100%)",
              border: "1px solid rgba(64,145,108,0.3)",
              borderRadius: "20px",
              width: "100%", maxWidth: "520px",
              maxHeight: "90vh", overflowY: "auto",
              boxShadow: "0 24px 60px rgba(0,0,0,0.5)",
              animation: "fadeUp 0.25s ease both",
            }}
          >
            <div style={{
              padding: "1.75rem 2rem 1.25rem",
              borderBottom: "1px solid rgba(255,255,255,0.08)",
              display: "flex", alignItems: "flex-start", justifyContent: "space-between",
            }}>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "4px" }}>
                  <span style={{ fontSize: "1.5rem" }}>🏗️</span>
                  <h3 style={{ fontSize: "1.25rem", fontFamily: "'Bebas Neue', sans-serif", letterSpacing: "1px" }}>
                    Nieuwe club aanvragen
                  </h3>
                </div>
                <p style={{ fontSize: "0.82rem", color: "var(--text-muted)", lineHeight: 1.5 }}>
                  Dien je aanvraag in — een admin beoordeelt deze en ontvangt automatisch een e-mail.
                </p>
              </div>
              <button
                onClick={closeModal}
                style={{
                  background: "rgba(255,255,255,0.07)", border: "1px solid rgba(255,255,255,0.1)",
                  borderRadius: "8px", color: "var(--text-muted)", cursor: "pointer",
                  fontSize: "1rem", padding: "4px 10px", lineHeight: 1, flexShrink: 0, marginLeft: "1rem",
                }}
              >✕</button>
            </div>

            <div style={{ padding: "1.5rem 2rem 2rem", display: "flex", flexDirection: "column", gap: "1.2rem" }}>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
                <div className="form-group">
                  <label>Clubnaam <span style={{ color: "var(--clay)", textTransform: "none" }}>*</span></label>
                  <input
                    type="text"
                    placeholder="bv. TC De Smash"
                    value={form.club_name}
                    onChange={(e) => setForm({ ...form, club_name: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Stad <span style={{ color: "var(--clay)", textTransform: "none" }}>*</span></label>
                  <input
                    type="text"
                    placeholder="bv. Antwerpen"
                    value={form.city}
                    onChange={(e) => setForm({ ...form, city: e.target.value })}
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Motivatie <span style={{ color: "var(--text-muted)", textTransform: "none", fontWeight: 400 }}>(optioneel)</span></label>
                <textarea
                  rows={3}
                  placeholder="Waarom wil je deze club aanmaken?"
                  value={form.motivation}
                  style={{
                    background: "rgba(0,0,0,0.25)", border: "1px solid var(--border)",
                    borderRadius: "8px", color: "var(--text)", fontFamily: "'DM Sans', sans-serif",
                    fontSize: "0.95rem", padding: "11px 14px", resize: "vertical",
                    minHeight: "90px", outline: "none", transition: "border-color 0.2s", width: "100%",
                  }}
                  onFocus={(e) => { e.currentTarget.style.borderColor = "var(--green-light)"; e.currentTarget.style.boxShadow = "0 0 0 3px rgba(64,145,108,0.12)"; }}
                  onBlur={(e) => { e.currentTarget.style.borderColor = "var(--border)"; e.currentTarget.style.boxShadow = "none"; }}
                  onChange={(e) => setForm({ ...form, motivation: e.target.value })}
                />
              </div>

              <div>
                <label style={{
                  display: "block", fontSize: "0.8rem", fontWeight: 600,
                  letterSpacing: "0.5px", textTransform: "uppercase",
                  color: "var(--text-muted)", marginBottom: "8px",
                }}>
                  Bijlagen <span style={{ color: "var(--text-muted)", textTransform: "none", fontWeight: 400 }}>
                    (optioneel · max {MAX_FILES} bestanden · {MAX_SIZE_MB} MB elk)
                  </span>
                </label>

                <div
                  onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                  onDragLeave={() => setDragOver(false)}
                  onDrop={(e) => { e.preventDefault(); setDragOver(false); addFiles(e.dataTransfer.files); }}
                  onClick={() => fileInputRef.current?.click()}
                  style={{
                    border: `2px dashed ${dragOver ? "var(--green-light)" : "rgba(255,255,255,0.15)"}`,
                    borderRadius: "12px", padding: "1.5rem", textAlign: "center", cursor: "pointer",
                    background: dragOver ? "rgba(64,145,108,0.08)" : "rgba(0,0,0,0.15)",
                    transition: "all 0.2s",
                  }}
                >
                  <div style={{ fontSize: "1.8rem", marginBottom: "6px" }}>📁</div>
                  <p style={{ fontSize: "0.88rem", color: "var(--text-muted)", lineHeight: 1.5 }}>
                    Sleep bestanden hierheen of <span style={{ color: "var(--green-light)", fontWeight: 600 }}>klik om te bladeren</span>
                  </p>
                  <p style={{ fontSize: "0.75rem", color: "rgba(143,181,154,0.5)", marginTop: "4px" }}>
                    PDF, Word, afbeeldingen…
                  </p>
                </div>

                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  style={{ display: "none" }}
                  onChange={(e) => { if (e.target.files) addFiles(e.target.files); e.target.value = ""; }}
                />

                {attachedFiles.length > 0 && (
                  <div style={{ marginTop: "0.75rem", display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                    {attachedFiles.map((af, i) => (
                      <div key={i} style={{
                        display: "flex", alignItems: "center", gap: "0.75rem",
                        background: "rgba(255,255,255,0.04)", border: "1px solid var(--border)",
                        borderRadius: "8px", padding: "0.5rem 0.75rem",
                      }}>
                        {af.preview
                          ? <img src={af.preview} alt="" style={{ width: 36, height: 36, borderRadius: 6, objectFit: "cover", flexShrink: 0 }} />
                          : <span style={{ fontSize: "1.4rem", flexShrink: 0 }}>{fileIcon(af.file.name)}</span>
                        }
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <p style={{ fontSize: "0.85rem", fontWeight: 500, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                            {af.file.name}
                          </p>
                          <p style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                            {formatBytes(af.file.size)}
                          </p>
                        </div>
                        <button
                          onClick={() => removeFile(i)}
                          style={{
                            background: "rgba(239,68,68,0.1)", border: "1px solid rgba(239,68,68,0.25)",
                            borderRadius: "6px", color: "#f87171", cursor: "pointer",
                            fontSize: "0.8rem", padding: "3px 8px", flexShrink: 0, fontFamily: "inherit",
                          }}
                        >✕</button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div style={{ display: "flex", gap: "0.75rem", justifyContent: "flex-end", paddingTop: "0.25rem" }}>
                <button
                  className="btn-secondary"
                  style={{ padding: "10px 22px", fontSize: "0.9rem" }}
                  disabled={requestLoading}
                  onClick={closeModal}
                >
                  Annuleren
                </button>
                <button
                  className="btn-submit"
                  style={{ padding: "10px 28px", fontSize: "0.9rem", width: "auto", marginTop: 0 }}
                  disabled={requestLoading || !form.club_name.trim() || !form.city.trim()}
                  onClick={handleRequestClub}
                >
                  {requestLoading ? "Bezig…" : "✓ Aanvraag indienen"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── JOIN REQUEST MODAL ── */}
      {joinTarget && (
        <div
          style={{
            position: "fixed", inset: 0, zIndex: 200,
            background: "rgba(0,0,0,0.72)", backdropFilter: "blur(6px)",
            display: "flex", alignItems: "center", justifyContent: "center", padding: "1rem",
          }}
          onClick={(e) => { if (e.target === e.currentTarget) { setJoinTarget(null); setJoinMotivation(""); } }}
        >
          <div style={{
            background: "linear-gradient(160deg, #1e3d2c 0%, #162e22 100%)",
            border: "1px solid rgba(64,145,108,0.3)",
            borderRadius: "20px",
            width: "100%", maxWidth: "440px",
            boxShadow: "0 24px 60px rgba(0,0,0,0.5)",
            animation: "fadeUp 0.25s ease both",
          }}>
            <div style={{
              padding: "1.5rem 1.75rem 1.1rem",
              borderBottom: "1px solid rgba(255,255,255,0.08)",
              display: "flex", alignItems: "flex-start", justifyContent: "space-between",
            }}>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "3px" }}>
                  <span style={{ fontSize: "1.3rem" }}>🏟️</span>
                  <h3 style={{ fontSize: "1.15rem", fontFamily: "'Bebas Neue', sans-serif", letterSpacing: "1px" }}>
                    Lid worden van {joinTarget.name}
                  </h3>
                </div>
                <p style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
                  📍 {joinTarget.city}
                </p>
              </div>
              <button onClick={() => { setJoinTarget(null); setJoinMotivation(""); }} style={{
                background: "rgba(255,255,255,0.07)", border: "1px solid rgba(255,255,255,0.1)",
                borderRadius: "8px", color: "var(--text-muted)", cursor: "pointer",
                fontSize: "1rem", padding: "4px 10px", flexShrink: 0, marginLeft: "1rem", fontFamily: "inherit",
              }}>✕</button>
            </div>

            <div style={{ padding: "1.4rem 1.75rem 1.75rem", display: "flex", flexDirection: "column", gap: "1rem" }}>
              <p style={{ fontSize: "0.85rem", color: "var(--text-muted)", lineHeight: 1.55 }}>
                Je aanvraag wordt doorgestuurd naar de club admin. Je ontvangt een e-mail zodra je aanvraag beoordeeld is.
              </p>

              <div className="form-group">
                <label>Motivatie <span style={{ color: "var(--text-muted)", textTransform: "none", fontWeight: 400 }}>(optioneel)</span></label>
                <textarea
                  rows={3}
                  placeholder="Waarom wil je lid worden van deze club?"
                  value={joinMotivation}
                  style={{
                    background: "rgba(0,0,0,0.25)", border: "1px solid var(--border)",
                    borderRadius: "8px", color: "var(--text)", fontFamily: "'DM Sans', sans-serif",
                    fontSize: "0.95rem", padding: "11px 14px", resize: "vertical",
                    minHeight: "80px", outline: "none", transition: "border-color 0.2s", width: "100%",
                  }}
                  onFocus={(e) => { e.currentTarget.style.borderColor = "var(--green-light)"; e.currentTarget.style.boxShadow = "0 0 0 3px rgba(64,145,108,0.12)"; }}
                  onBlur={(e) => { e.currentTarget.style.borderColor = "var(--border)"; e.currentTarget.style.boxShadow = "none"; }}
                  onChange={(e) => setJoinMotivation(e.target.value)}
                />
              </div>

              <div style={{ display: "flex", gap: "0.75rem", justifyContent: "flex-end" }}>
                <button
                  className="btn-secondary"
                  style={{ padding: "9px 20px", fontSize: "0.9rem" }}
                  disabled={joinLoading}
                  onClick={() => { setJoinTarget(null); setJoinMotivation(""); }}
                >
                  Annuleren
                </button>
                <button
                  className="btn-submit"
                  style={{ padding: "9px 24px", fontSize: "0.9rem", width: "auto", marginTop: 0 }}
                  disabled={joinLoading}
                  onClick={handleSubmitJoinRequest}
                >
                  {joinLoading ? "Bezig…" : "✓ Aanvraag versturen"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}