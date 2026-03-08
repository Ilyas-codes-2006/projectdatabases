import { useNavigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useMessageContext } from "../context/MessageContext";

export default function Navbar() {
  const navigate = useNavigate();
  const location = useLocation();
  const { loggedInUser, isAdmin, logout } = useAuth();
  const { showMessage, clearMessage } = useMessageContext();

  const handleLogout = () => {
    logout();
    showMessage("Je bent uitgelogd.", "success");
    navigate("/");
  };

  return (
    <nav className="navbar">
      <div className="nav-brand" onClick={() => navigate("/")}>
        <span className="nav-logo">🎾</span>
        <span className="nav-title">MatchUp</span>
      </div>

      <div className="nav-links">
        <button
          className={`nav-btn ${location.pathname === "/" ? "active" : ""}`}
          onClick={() => navigate("/")}
        >
          Home
        </button>

        {!loggedInUser ? (
          <>
            <button
              className={`nav-btn ${location.pathname === "/login" ? "active" : ""}`}
              onClick={() => { clearMessage(); navigate("/login"); }}
            >
              Login
            </button>
            <button
              className="nav-btn nav-cta"
              onClick={() => { clearMessage(); navigate("/register"); }}
            >
              Join Now
            </button>
          </>
        ) : (
          <>
            {isAdmin && (
              <button
                className={`nav-btn ${location.pathname === "/admin" ? "active" : ""}`}
                onClick={() => navigate("/admin")}
              >
                Admin
              </button>
            )}
            <span className="nav-user">👋 {loggedInUser}</span>
            <button className="nav-btn" onClick={handleLogout}>
              Logout
            </button>
          </>
        )}
      </div>
    </nav>
  );
}