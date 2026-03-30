import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useState, useEffect, useRef} from "react";

type Notification = {
    type: "join_request" | "team_event";
    message: string;
};

export default function Navbar() {
  const navigate = useNavigate();
  const location = useLocation();
  const { loggedInUser, isAdmin, isClubAdmin, myClubName, logout } = useAuth();

  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const active = (path: string) => location.pathname === path ? "active" : "";

  const handleLogout = () => {
    logout();
    navigate("/", { state: { message: "Je bent uitgelogd.", type: "success" } });
  };

  useEffect(() => {
  if (!loggedInUser) return;

  const fetchNotifications = async () => {
    const token = localStorage.getItem("token");
    if (!token) return;
    try {
      const res = await fetch("/api/notifications", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setNotifications(data);
      }
    } catch { /* silent */ }
  };

  fetchNotifications();
  const interval = setInterval(fetchNotifications, 10000);
  return () => clearInterval(interval);
  }, [loggedInUser]);

  const markAsRead = async () => {
    const token = localStorage.getItem("token");
    if (!token) return;
    try {
      await fetch("/api/notifications/read", {
        method: "PATCH",
        headers: { Authorization: `Bearer ${token}` },
      });
      setNotifications([]);
    } catch { /* silent */ }
  };

  const handleBellClick = () => {
    setDropdownOpen((prev) => {
      if (prev) markAsRead();
      return !prev;
    });
  };

  // Sluit dropdown bij klikken buiten
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
        markAsRead();
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  return (
    <nav className="navbar">
      <div className="nav-brand" onClick={() => navigate("/")}>
        <span className="nav-logo">🎾</span>
        <span className="nav-title">MatchUp</span>
      </div>

      <div className="nav-links">
        <button className={`nav-btn ${active("/")}`} onClick={() => navigate("/")}>
          Home
        </button>

        {!loggedInUser ? (
          <>
            <button className={`nav-btn ${active("/login")}`} onClick={() => navigate("/login")}>
              Login
            </button>
            <button className="nav-btn nav-cta" onClick={() => navigate("/register")}>
              Join Now
            </button>
          </>
        ) : (
          <>
            {isAdmin && (
              <button className={`nav-btn ${active("/admin")}`} onClick={() => navigate("/admin")}>
                Admin
              </button>
            )}
            <button className={`nav-btn ${active("/teams")}`} onClick={() => navigate("/teams")}>
              My Teams
            </button>

            {isClubAdmin ? (
              <button
                className={`nav-btn ${active("/my-club")}`}
                onClick={() => navigate("/my-club")}
                title={myClubName ?? "My Club"}
                style={{ position: "relative" }}
              >
                My Club
              </button>
            ) : (
              <button className={`nav-btn ${active("/clubs")}`} onClick={() => navigate("/clubs")}>
                Clubs
              </button>
            )}

            {/* ── NOTIFICATIE BELLETJE ── */}
            <div ref={dropdownRef} style={{ position: "relative" }}>
              <button
                onClick={() => handleBellClick()}
                style={{
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                  fontSize: "1.3rem",
                  padding: "8px",
                  position: "relative",
                  lineHeight: 1,
                }}
              >
                🔔
                {notifications.length > 0 && (
                  <span style={{
                    position: "absolute",
                    top: 2,
                    right: 2,
                    background: "#e53e3e",
                    color: "#fff",
                    borderRadius: "50%",
                    width: 18,
                    height: 18,
                    fontSize: "0.65rem",
                    fontWeight: 700,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}>
                    {notifications.length}
                  </span>
                )}
              </button>

              {/* ── DROPDOWN ── */}
              {dropdownOpen && (
                <div style={{
                  position: "absolute",
                  top: "calc(100% + 8px)",
                  right: 0,
                  background: "#1b3a27",
                  border: "1px solid rgba(255,255,255,0.12)",
                  borderRadius: "12px",
                  minWidth: 280,
                  boxShadow: "0 8px 24px rgba(0,0,0,0.4)",
                  zIndex: 200,
                  overflow: "hidden",
                }}>
                  <div style={{
                    padding: "12px 16px",
                    borderBottom: "1px solid rgba(255,255,255,0.1)",
                    fontSize: "0.8rem",
                    fontWeight: 600,
                    letterSpacing: "0.5px",
                    textTransform: "uppercase",
                    color: "#8fb59a",
                  }}>
                    notifications
                  </div>

                  {notifications.length === 0 ? (
                    <div style={{ padding: "16px", color: "#8fb59a", fontSize: "0.9rem", textAlign: "center" }}>
                      Geen openstaande verzoeken
                    </div>
                  ) : (
                    notifications.map((n, i) => (
                      <div key={i} style={{
                        padding: "12px 16px",
                        borderBottom: i < notifications.length - 1 ? "1px solid rgba(255,255,255,0.06)" : "none",
                        fontSize: "0.9rem",
                        color: "#f4f9f5",
                      }}>
                        {n.message}
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
            <button className={`nav-btn nav-user-btn ${active("/profile")}`} onClick={() => navigate("/profile")}>
              👋 {loggedInUser}
            </button>
            <button className="nav-btn" onClick={handleLogout}>
              Logout
            </button>
          </>
        )}
      </div>
    </nav>
  );
}