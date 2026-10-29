import { api } from "./client";

export const getCsrf = () => api("/csrf/");
export const getCurrentUser = () => api("/auth/me/");
export const login = (username, password) =>
  api("/auth/login/", { method: "POST", body: { username, password } });
export const logout = () => api("/auth/logout/", { method: "POST" });
  api("/auth/signup/", { method: "POST", body: userData });
export const signUp = (form) => api("/auth/signup/", { method: "POST", body: form });
