import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const navigate = useNavigate();
  const location = useLocation();
  const { loggedInUser, isAdmin, isClubAdmin, myClubName, logout } = useAuth();

  const active = (path: string) => location.pathname === path ? "active" : "";

  const handleLogout = () => {
    logout();
    navigate("/", { state: { message: "Je bent uitgelogd.", type: "success" } });
  };

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
              My Team
            </button>
            {isClubAdmin ? (
              <button
                className={`nav-btn ${active("/my-club")}`}
                onClick={() => navigate("/my-club")}
                title={myClubName ?? "My Club"}
                style={{ position: "relative" }}
              >
                🏟️ My Club
              </button>
            ) : (
              <button className={`nav-btn ${active("/clubs")}`} onClick={() => navigate("/clubs")}>
                Clubs
              </button>
            )}
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