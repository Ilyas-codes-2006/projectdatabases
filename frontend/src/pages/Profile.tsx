import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useNavigate } from "react-router-dom";

interface ProfileData {
  first_name: string;
  last_name: string;
  email: string;
  bio: string;
  photo_url: string;
  date_of_birth: string;
}

export default function Profile() {
  const {loggedInUser} = useAuth();
  const navigate = useNavigate();
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [editing, setEditing] = useState(false);
  const [bio, setBio] = useState("");
  const [photoUrl, setPhotoUrl] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [showEditMenu, setShowEditMenu] = useState(false);

  useEffect(() => {
    if (!loggedInUser) {
      navigate("/login");
      return;
    }
    fetchProfile();
  }, [loggedInUser]);

  const fetchProfile = async () => {
    try {
      const res = await fetch("/api/profile", {
        headers: {Authorization: `Bearer ${localStorage.getItem("token")}`},
      });
      if (!res.ok) throw new Error("Failed to load profile");
      const data = await res.json();
      setProfile(data);
      setBio(data.bio || "");
      setPhotoUrl(data.photo_url || "");
    } catch {
      setError("Could not load profile.");
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setError("");
    try {
      const res = await fetch("/api/profile", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({bio, photo_url: photoUrl}),
      });
      if (!res.ok) throw new Error("Failed to save");
      setProfile((prev) => (prev ? {...prev, bio, photo_url: photoUrl} : prev));
      setEditing(false);
    } catch {
      setError("Could not save profile.");
    } finally {
      setSaving(false);
    }
  };

  if (!profile) {
    return (
        <div className="profile-wrapper">
          <p style={{textAlign: "center", color: "var(--text-muted)"}}>
            {error || "Loading profile…"}
          </p>
        </div>
    );
  }

  return (
      <div className="profile-wrapper">
        <div className="profile-card">
          {/* Photo */}
          <div className="profile-photo-section">
            {profile.photo_url ? (
                <img src={profile.photo_url} alt="Profile" className="profile-photo"/>
            ) : (
                <div className="profile-photo-placeholder">
                  {profile.first_name[0]}
                  {profile.last_name[0]}
                </div>
            )}
          </div>

          {/* Info */}
          <h2 className="profile-name">
            {profile.first_name} {profile.last_name}
          </h2>
          <p className="profile-email">{profile.email}</p>
          <p className="profile-dob">
            {new Date(profile.date_of_birth).toLocaleDateString()}
          </p>
          {/* Edit Profile knop */}
          <button
            className="btn-secondary"
            onClick={() => setShowEditMenu(!showEditMenu)}
          >
            Edit Profile
          </button>
          {/* Mini kader / popup met keuzes */}
          {showEditMenu && (
            <div className="edit-menu">
              <button onClick={() => navigate("/profile/change-name")}>Edit Name</button>
              <button onClick={() => navigate("/profile/change-email")}>Edit Email</button>
              <button onClick={() => navigate("/profile/change-birthday")}>Edit Birthday</button>
            </div>
          )}
          <hr className="profile-divider"/>

          {/* Bio */}
          <div className="profile-bio-section">
            <h3 className="profile-section-title">More about yourself</h3>
            {editing ? (
              <>
                <textarea
                  className="profile-bio-input"
                  rows={4}
                  value={bio}
                  onChange={(e) => setBio(e.target.value)}
                  placeholder="Tell us about yourself…"
                />
                <div className="profile-section-title" style={{ marginTop: "1rem" }}>
                  Photo URL
                </div>
                <input
                  className="profile-url-input"
                  type="text"
                  value={photoUrl}
                  onChange={(e) => setPhotoUrl(e.target.value)}
                  placeholder="https://example.com/photo.jpg"
                />
                {error && <p className="profile-error">{error}</p>}
                <div className="profile-actions">
                  <button className="btn-submit" onClick={handleSave} disabled={saving}>
                    {saving ? "Saving…" : "Save"}
                  </button>
                  <button
                    className="btn-secondary"
                    onClick={() => {
                      setEditing(false);
                      setBio(profile.bio);
                      setPhotoUrl(profile.photo_url);
                      setError("");
                    }}
                  >
                    Cancel
                  </button>
                </div>
              </>
            ) : (
              <>
                <p className="profile-bio-text">
                  {profile.bio || "No bio yet. Click edit to add one!"}
                </p>
                <button
                  className="btn-primary profile-edit-btn"
                  onClick={() => setEditing(true)}
                >
                  ✏️ More about yourself
                </button>
              </>
            )}
          </div>
        </div>
      </div>
  );
}