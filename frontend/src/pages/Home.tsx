import { useNavigate, useLocation } from "react-router-dom";
import { useEffect } from "react";
import { useAuth } from "../context/AuthContext";
import { useMessage } from "../hooks/useMessage";
import MessageBanner from "../components/MessageBanner";
import courtsBg from "../assets/court.jpeg";
import Calendar from "../components/Calendar";
import Ladder from "../components/Ladder";

export default function Home() {
  const navigate = useNavigate();
  const location = useLocation();
  const { loggedInUser } = useAuth();
  const { message, clearMessage, showMessage } = useMessage();

  useEffect(() => {
    if (location.state?.message) {
      showMessage(location.state.message, location.state.type ?? "success");
      window.history.replaceState({}, "");
    }
  }, [location.state]);

  return (
    <>
      <MessageBanner message={message} onClose={clearMessage} />

      <main className="hero">
        <div
          className="hero-bg"
          style={{ backgroundImage: `url(${courtsBg})` }}
        />
        <div className="court-lines" />
        <div className="hero-content">
          <p className="hero-eyebrow">Your Club. Your Game.</p>
          <h1 className="hero-title">
            Manage your tennis &<br />
            padel experience
          </h1>
          <p className="hero-subtitle">
            Manage and view your schedule, track your progress, connect with
            fellow players — all in one place for your club.
          </p>

          {!loggedInUser ? (
            <div className="hero-actions">
              <button
                className="btn-primary"
                onClick={() => navigate("/register")}
              >
                Get Started
              </button>
              <button
                className="btn-secondary"
                onClick={() => navigate("/login")}
              >
                Sign In
              </button>
            </div>
          ) : (
            <div className="hero-actions">
              <button className="btn-primary">Set your availability</button>
              <button className="btn-secondary">View Schedule</button>
            </div>
          )}
        </div>
        {loggedInUser && (
          <div className="hero-dashboard">
            <div className="hero-ladder">
              <Ladder />
            </div>

            <div className="hero-calendar-wrapper">
              <Calendar showMessage={showMessage} />
            </div>
          </div>
        )}
        {!loggedInUser && (
          <div className="features">
            <div className="feature-card">
              <span className="feature-icon">🏆</span>
              <h3>Track Progress</h3>
              <p>Monitor your skill development and match history over time.</p>
            </div>
            <div className="feature-card">
              <span className="feature-icon">📅</span>
              <h3>Manage Schedule</h3>
              <p>Set your availability per day and view your match schedule.</p>
            </div>
            <div className="feature-card">
              <span className="feature-icon">🤝</span>
              <h3>Find Partners</h3>
              <p>Match with players at your level and grow the community.</p>
            </div>
          </div>
        )}
      </main>
    </>
  );
}
