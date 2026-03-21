import { createContext, useContext, useState, useEffect, type ReactNode } from "react";

interface AuthContextType {
  loggedInUser: string | null;
  isAdmin: boolean;
  isClubAdmin: boolean;
  myClubName: string | null;
  myClubId: number | null;
  login: (token: string, name: string, isAdmin: boolean) => void;
  logout: () => void;
  refreshClubStatus: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [loggedInUser, setLoggedInUser] = useState<string | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [isClubAdmin, setIsClubAdmin] = useState(false);
  const [myClubName, setMyClubName] = useState<string | null>(null);
  const [myClubId, setMyClubId] = useState<number | null>(null);

  const fetchClubStatus = async (token: string) => {
    try {
      const res = await fetch("/api/profile/club-status", {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      setIsClubAdmin(data.is_club_admin ?? false);
      setMyClubName(data.club_name ?? null);
      setMyClubId(data.club_id ?? null);
    } catch {
      setIsClubAdmin(false);
      setMyClubName(null);
      setMyClubId(null);
    }
  };

  useEffect(() => {
    const token = localStorage.getItem("token");
    const name = localStorage.getItem("userName");
    const admin = localStorage.getItem("is_admin") === "true";
    if (token && name) {
      setLoggedInUser(name);
      setIsAdmin(admin);
      fetchClubStatus(token);
    }
  }, []);

  const login = (token: string, name: string, admin: boolean) => {
    localStorage.setItem("token", token);
    localStorage.setItem("userName", name);
    localStorage.setItem("is_admin", String(admin));
    setLoggedInUser(name);
    setIsAdmin(admin);
    fetchClubStatus(token);
  };

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("userName");
    localStorage.removeItem("is_admin");
    setLoggedInUser(null);
    setIsAdmin(false);
    setIsClubAdmin(false);
    setMyClubName(null);
    setMyClubId(null);
  };

  const refreshClubStatus = async () => {
    const token = localStorage.getItem("token");
    if (token) await fetchClubStatus(token);
  };

  return (
    <AuthContext.Provider value={{ loggedInUser, isAdmin, isClubAdmin, myClubName, myClubId, login, logout, refreshClubStatus }}>
      {children}
    </AuthContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}