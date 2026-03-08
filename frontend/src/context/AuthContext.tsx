import { createContext, useContext, useState, useEffect, type ReactNode } from "react";

interface AuthContextType {
  loggedInUser: string | null;
  isAdmin: boolean;
  login: (token: string, name: string, isAdmin: boolean) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [loggedInUser, setLoggedInUser] = useState<string | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("token");
    const name = localStorage.getItem("userName");
    const admin = localStorage.getItem("is_admin") === "true";
    if (token && name) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setLoggedInUser(name);
      setIsAdmin(admin);
    }
  }, []);

  const login = (token: string, name: string, admin: boolean) => {
    localStorage.setItem("token", token);
    localStorage.setItem("userName", name);
    localStorage.setItem("is_admin", String(admin));
    setLoggedInUser(name);
    setIsAdmin(admin);
  };

  const logout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("userName");
    localStorage.removeItem("is_admin");
    setLoggedInUser(null);
    setIsAdmin(false);
  };

  return (
    <AuthContext.Provider value={{ loggedInUser, isAdmin, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}