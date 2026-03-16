import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useMessage } from "../hooks/useMessage";
import MessageBanner from "../components/MessageBanner";

type AdminUser = {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  date_of_birth: string;
  created_at: string;
  is_admin?: boolean;
};

type Club = { id: number; name: string; city: string };
type Team = { id: number; name: string; member_count: number };

const authHeader = () => ({ Authorization: `Bearer ${localStorage.getItem("token")}` });

export default function Admin() {
  const navigate = useNavigate();
  const { isAdmin } = useAuth();
  const { message, clearMessage, showMessage } = useMessage();
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(false);
  const [clubs, setClubs] = useState<Club[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);

  // modal state
  const [editingUser, setEditingUser] = useState<AdminUser | null>(null);
  const [selectedClub, setSelectedClub] = useState<number | "">("");
  const [selectedTeam, setSelectedTeam] = useState<number | "">("");
  const [saving, setSaving] = useState(false);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"club" | "team">("club");

const handleDelete = async (userId: number) => {
  if (!window.confirm("Are you sure you want to delete this user? This action cannot be undone.")) {
    return;
  }

  try {
    const res = await fetch(`/api/admin/users/${userId}`, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${localStorage.getItem("token")}`
      },
    });

    if (res.ok) {
        // Remove the deleted user from the local state
        setUsers(users.filter((u) => u.id !== userId));
        showMessage("User deleted successfully", "success");
    } else {
        const data = await res.json();
        showMessage(data.error || "Failed to delete user", "error");
    }
  } catch (err) {
    showMessage("Network error occurred", "error");
  }
};


  useEffect(() => {
    if (!isAdmin) navigate("/");
  }, [isAdmin, navigate]);

    useEffect(() => {
    fetchUsers();
    fetchClubs();
    fetchTeams();
  }, []);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/admin/users", { headers: authHeader() });
      const data = await res.json();
      if (res.ok) setUsers(data);
      else showMessage(data.error || "Kon gebruikers niet laden", "error");
    } catch { showMessage("Kan geen verbinding maken met de server", "error"); }
    finally { setLoading(false); }
  };

  const fetchClubs = async () => {
    const res = await fetch("/api/admin/clubs", { headers: authHeader() });
    if (res.ok) setClubs(await res.json());
  };

  const fetchTeams = async () => {
    const res = await fetch("/api/admin/teams", { headers: authHeader() });
    if (res.ok) setTeams(await res.json());
  };

  const openEdit = async (user: AdminUser) => {
    setEditingUser(user);
    setActiveTab("club");
    setSelectedClub("");
    setSelectedTeam("");

    setDetailsLoading(true);
    try {
      const res = await fetch(`/api/admin/users/${user.id}/details`, { headers: authHeader() });
      if (res.ok) {
        const d = await res.json();
        setSelectedClub(d.club_id ?? "");
        setSelectedTeam(d.team_id ?? "");
      }
    } catch { /* silent */ }
    finally { setDetailsLoading(false); }
  };

  const closeEdit = () => setEditingUser(null);

  const handleSaveClub = async () => {
    if (!editingUser) return;
    setSaving(true);
    clearMessage();
    try {
      const res = await fetch(`/api/admin/users/${editingUser.id}/club`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", ...authHeader() },
        body: JSON.stringify({ club_id: selectedClub === "" ? null : selectedClub }),
      });
      const data = await res.json();
      if (res.ok) { showMessage("Club succesvol bijgewerkt", "success"); closeEdit(); }
      else showMessage(data.error || "Bijwerken mislukt", "error");
    } catch { showMessage("Kan geen verbinding maken met de server", "error"); }
    finally { setSaving(false); }
  };

  const handleSaveTeam = async () => {
    if (!editingUser) return;
    setSaving(true);
    clearMessage();
    try {
      const res = await fetch(`/api/admin/users/${editingUser.id}/team`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", ...authHeader() },
        body: JSON.stringify({ team_id: selectedTeam === "" ? null : selectedTeam }),
      });
      const data = await res.json();
      if (res.ok) { showMessage("Team succesvol bijgewerkt", "success"); closeEdit(); fetchTeams(); }
      else showMessage(data.error || "Bijwerken mislukt", "error");
    } catch { showMessage("Kan geen verbinding maken met de server", "error"); }
    finally { setSaving(false); }
  };

  return (
    <div className="admin-wrapper">
      <MessageBanner message={message} onClose={clearMessage} />
      {/* ── MODAL ── */}
      {editingUser && (
        <div style={s.overlay} onClick={closeEdit}>
          <div style={s.modal} onClick={(e) => e.stopPropagation()}>

            <div style={s.modalHeader}>
              <div>
                <p style={s.modalSub}>Gebruiker aanpassen</p>
                <h3 style={s.modalTitle}>{editingUser.first_name} {editingUser.last_name}</h3>
              </div>
              <button style={s.closeBtn} onClick={closeEdit}>✕</button>
            </div>

            <div style={s.tabs}>
              {(["club", "team"] as const).map((tab) => (
                <button
                  key={tab}
                  style={{ ...s.tab, ...(activeTab === tab ? s.tabActive : {}) }}
                  onClick={() => setActiveTab(tab)}
                >
                  {tab === "club" ? "🏟️ Club" : "👥 Team"}
                </button>
              ))}
            </div>

            <div style={s.modalBody}>

              {detailsLoading ? (
                <p style={{ color: "#8fb59a", textAlign: "center" }}>Laden…</p>
              ) : (
                <>
                  {/* ── TAB: CLUB ── */}
                  {activeTab === "club" && (
                    <>
                      <div style={s.formGroup}>
                        <label style={s.label}>Club</label>
                        <select
                          style={s.select}
                          value={selectedClub}
                          onChange={(e) => setSelectedClub(e.target.value === "" ? "" : Number(e.target.value))}
                        >
                          <option value="">— Geen club —</option>
                          {clubs.map((c) => (
                            <option key={c.id} value={c.id}>{c.name} ({c.city})</option>
                          ))}
                        </select>
                        <p style={s.hint}>Selecteer "Geen club" om de gebruiker uit zijn club te verwijderen.</p>
                      </div>
                      <div style={s.modalFooter}>
                        <button style={s.cancelBtn} onClick={closeEdit} disabled={saving}>Annuleren</button>
                        <button style={s.saveBtn} onClick={handleSaveClub} disabled={saving}>
                          {saving ? "Opslaan…" : "Opslaan"}
                        </button>
                      </div>
                    </>
                  )}

                  {/* ── TAB: TEAM ── */}
                  {activeTab === "team" && (
                    <>
                      <div style={s.formGroup}>
                        <label style={s.label}>Team</label>
                        <select
                          style={s.select}
                          value={selectedTeam}
                          onChange={(e) => setSelectedTeam(e.target.value === "" ? "" : Number(e.target.value))}
                        >
                          <option value="">— Geen team —</option>
                          {teams.map((t) => (
                            <option
                              key={t.id}
                              value={t.id}
                              disabled={t.member_count >= 2 && t.id !== selectedTeam}
                            >
                              {t.name} — {t.member_count}/2 spelers
                              {t.member_count >= 2 && t.id !== selectedTeam ? " (vol)" : ""}
                            </option>
                          ))}
                        </select>
                        <p style={s.hint}>Selecteer "Geen team" om de gebruiker uit zijn team te verwijderen.</p>
                      </div>
                      <div style={s.modalFooter}>
                        <button style={s.cancelBtn} onClick={closeEdit} disabled={saving}>Annuleren</button>
                        <button style={s.saveBtn} onClick={handleSaveTeam} disabled={saving}>
                          {saving ? "Opslaan…" : "Opslaan"}
                        </button>
                      </div>
                    </>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ── TABEL ── */}
      <div className="admin-container">
        <div className="admin-header">
          <h1>Admin Dashboard</h1>
          <p>Manage registered users</p>
        </div>
        <div className="admin-card">
          <div className="admin-card-header">
            <h2>Users</h2>
            <p>{users.length} registered user{users.length !== 1 ? "s" : ""}</p>
          </div>
          <div className="admin-table-wrapper">
            {loading ? (
              <p style={{ padding: "1rem", textAlign: "center" }}>Laden…</p>
            ) : (
              <table className="admin-table">
                <thead>
                  <tr>
                    <th>First Name</th>
                    <th>Last Name</th>
                    <th>Email</th>
                    <th>Date of Birth</th>
                    <th>Created At</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {users.length > 0 ? (
                    users.map((user) => (
                      <tr key={user.id}>
                        <td>{user.first_name}</td>
                        <td>{user.last_name}</td>
                        <td>{user.email}</td>
                        <td>{new Date(user.date_of_birth).toLocaleDateString()}</td>
                        <td>{new Date(user.created_at).toLocaleDateString()}</td>
                        <td>
                          <button
                            className="edit-btn"
                            onClick={() => alert("Edit user " + user.id)}
                            style={{ marginRight: "8px" }}
                          >
                            Edit
                          </button>
                          <button
                            className="delete-btn"
                            onClick={() => handleDelete(user.id)}
                            style={{ backgroundColor: "#dc3545", color: "white", border: "none", padding: "5px 10px", borderRadius: "4px", cursor: "pointer" }}
                          >
                            Delete
                          </button>
                        </td>

                      </tr>
                    ))
                  ) : (
                    <tr><td colSpan={6} className="empty-cell">No users found.</td></tr>
                  )}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

const s: Record<string, React.CSSProperties> = {
  overlay: {
    position: "fixed", inset: 0,
    background: "rgba(0,0,0,0.65)",
    backdropFilter: "blur(4px)",
    display: "flex", alignItems: "center", justifyContent: "center",
    zIndex: 999, padding: "1rem",
  },
  modal: {
    background: "#1b3a27",
    border: "1px solid rgba(255,255,255,0.12)",
    borderRadius: "16px",
    width: "100%", maxWidth: "460px",
    boxShadow: "0 24px 48px rgba(0,0,0,0.5)",
  },
  modalHeader: {
    display: "flex", justifyContent: "space-between", alignItems: "flex-start",
    padding: "1.5rem 1.5rem 0",
  },
  modalSub: { fontSize: "0.75rem", color: "#8fb59a", textTransform: "uppercase", letterSpacing: "1px", margin: 0 },
  modalTitle: { fontSize: "1.2rem", fontWeight: 700, color: "#f4f9f5", margin: "4px 0 0" },
  closeBtn: {
    background: "none", border: "none", color: "#8fb59a",
    fontSize: "1.2rem", cursor: "pointer", padding: "4px 8px", borderRadius: "6px",
  },
  tabs: {
    display: "flex", gap: "4px",
    padding: "1rem 1.5rem 0",
    borderBottom: "1px solid rgba(255,255,255,0.1)",
  },
  tab: {
    background: "none", border: "none",
    color: "#8fb59a", fontFamily: "DM Sans, sans-serif",
    fontSize: "0.85rem", fontWeight: 500,
    padding: "8px 14px", borderRadius: "8px 8px 0 0",
    cursor: "pointer", transition: "all 0.15s",
  },
  tabActive: {
    background: "rgba(64,145,108,0.15)",
    color: "#f4f9f5",
    borderBottom: "2px solid #40916c",
  },
  modalBody: {
    padding: "1.5rem",
    display: "flex", flexDirection: "column", gap: "1rem",
  },
  formGroup: { display: "flex", flexDirection: "column", gap: "6px" },
  label: {
    fontSize: "0.75rem", fontWeight: 600, letterSpacing: "0.5px",
    textTransform: "uppercase", color: "#8fb59a",
  },
  select: {
    background: "#0d1b12",
    border: "1px solid rgba(255,255,255,0.1)",
    borderRadius: "8px", color: "#f4f9f5",
    fontFamily: "DM Sans, sans-serif",
    fontSize: "0.95rem", padding: "10px 12px",
    outline: "none", width: "100%", cursor: "pointer",
  },
  hint: { fontSize: "0.8rem", color: "#8fb59a", margin: 0 },
  modalFooter: { display: "flex", justifyContent: "flex-end", gap: "12px", marginTop: "0.5rem" },
  cancelBtn: {
    background: "transparent", border: "1px solid rgba(255,255,255,0.15)",
    borderRadius: "8px", color: "#8fb59a",
    fontFamily: "DM Sans, sans-serif", fontSize: "0.95rem",
    fontWeight: 500, padding: "10px 20px", cursor: "pointer",
  },
  saveBtn: {
    background: "#2d6a4f", border: "none",
    borderRadius: "8px", color: "#fff",
    fontFamily: "DM Sans, sans-serif", fontSize: "0.95rem",
    fontWeight: 600, padding: "10px 24px", cursor: "pointer",
  },
};