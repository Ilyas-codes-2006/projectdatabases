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
};

export default function Admin() {
  const navigate = useNavigate();
  const { isAdmin } = useAuth();
  const { message, clearMessage, showMessage } = useMessage();
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [loading, setLoading] = useState(false);
  const [pendingCount, setPendingCount] = useState<number | null>(null);

  useEffect(() => {
    if (!isAdmin) navigate("/");
  }, [isAdmin, navigate]);

  useEffect(() => {
    const fetchUsers = async () => {
      setLoading(true);
      try {
        const res = await fetch("/api/admin/users", {
          headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
        });
        const data = await res.json();
        if (res.ok) setUsers(data);
        else showMessage(data.error || "Kon gebruikers niet laden", "error");
      } catch {
        showMessage("Kan geen verbinding maken met de server", "error");
      } finally {
        setLoading(false);
      }
    };

    const fetchPendingCount = async () => {
      try {
        const res = await fetch("/api/admin/club-requests", {
          headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
        });
        const data = await res.json();
        if (data.success) {
          setPendingCount(data.requests.filter((r: { status: string }) => r.status === "pending").length);
        }
      } catch { /* stil falen */ }
    };

    fetchUsers();
    fetchPendingCount();
  }, []);

  return (
    <div className="admin-wrapper">
      <MessageBanner message={message} onClose={clearMessage} />
      <div className="admin-container">
        <div className="admin-header">
          <h1>Admin Dashboard</h1>
          <p>Manage registered users</p>
        </div>

        {/* Navigatiekaarten */}
        <div style={{ display: "flex", gap: "1rem", marginBottom: "2rem", flexWrap: "wrap" }}>
          <button
            onClick={() => navigate("/admin/club-requests")}
            style={{
              display: "flex", alignItems: "center", gap: "0.75rem",
              background: "rgba(255,255,255,0.05)", border: "1px solid rgba(255,255,255,0.12)",
              borderRadius: "12px", padding: "1rem 1.5rem", cursor: "pointer",
              color: "var(--text)", fontFamily: "inherit", fontSize: "0.95rem",
              transition: "background 0.15s", textAlign: "left",
            }}
            onMouseOver={(e) => (e.currentTarget.style.background = "rgba(64,145,108,0.12)")}
            onMouseOut={(e) => (e.currentTarget.style.background = "rgba(255,255,255,0.05)")}
          >
            <span style={{ fontSize: "1.6rem" }}>🏗️</span>
            <div>
              <div style={{ fontWeight: 600, marginBottom: "2px" }}>
                Club-aanvragen
                {pendingCount !== null && pendingCount > 0 && (
                  <span style={{
                    marginLeft: "8px", background: "#f59e0b", color: "#000",
                    borderRadius: "20px", fontSize: "0.7rem", fontWeight: 700,
                    padding: "2px 8px",
                  }}>
                    {pendingCount} nieuw
                  </span>
                )}
              </div>
              <div style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>Beoordeel aanvragen voor nieuwe clubs</div>
            </div>
            <span style={{ marginLeft: "auto", color: "var(--text-muted)" }}>→</span>
          </button>
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
                          <button className="edit-btn" onClick={() => alert("Edit user " + user.id)}>
                            Edit
                          </button>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={6} className="empty-cell">No users found.</td>
                    </tr>
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