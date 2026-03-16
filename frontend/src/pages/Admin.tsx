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
    fetchUsers();
  }, []);

  return (
    <div className="admin-wrapper">
      <MessageBanner message={message} onClose={clearMessage} />
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