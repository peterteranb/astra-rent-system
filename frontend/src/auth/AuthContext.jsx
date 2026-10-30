import { createContext, useContext, useEffect, useState } from "react";
import { getCsrf, getCurrentUser, login as apiLogin, logout as apiLogout } from "../api/auth";

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

// Mismo reparto que rentals/views/home.py
export function homePathFor(role) {
  if (role === "administrador") return "/manager";
  if (role === "operador") return "/staff/reservations";
  if (role === "mantenimiento") return "/maintenance";
  if (role === "operador") return "/";
  return "/";
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    const expire = () => setUser(null);
    window.addEventListener("session-expired", expire);

    const initializeSession = async () => {
      try {
        await getCsrf();
        const { data } = await getCurrentUser();
        if (active) setUser(data);
      } catch {
        // Sin una sesión activa (o con Django aún apagado), el login sigue accesible.
        if (active) setUser(null);
      } finally {
        if (active) setLoading(false);
      }
    };

    initializeSession();
    return () => {
      active = false;
      window.removeEventListener("session-expired", expire);
    };
  }, []);

  const login = async (username, password) => {
    const { data } = await apiLogin(username, password);
    setUser(data);
    return data;
  };

  const logout = async () => {
    await apiLogout();
    setUser(null);
    await getCsrf();
  };

  const refresh = async () => {
    const { data } = await getCurrentUser();
    setUser(data);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, refresh }}>
      {children}
    </AuthContext.Provider>
  );
}