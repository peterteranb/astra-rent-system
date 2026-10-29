import { createContext, useContext, useEffect, useState } from "react";
import { api } from "../api/client";

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        await api("/csrf/");
        setUser((await api("/auth/me/")).data);
      } catch {
        setUser(null);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  async function login(username, password) {
    const { data } = await api("/auth/login/", { method: "POST", body: { username, password } });
    setUser(data);
    return data;
  }

  async function logout() {
    await api("/auth/logout/", { method: "POST" });
    await api("/csrf/"); // Django cambia el token al cerrar sesión
    setUser(null);
  }

  return <AuthContext.Provider value={{ user, loading, login, logout }}>{children}</AuthContext.Provider>;
}