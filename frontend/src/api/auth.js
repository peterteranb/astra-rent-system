import { api } from "./client";

export const getCsrf = () => api("/csrf/");
export const getCurrentUser = () => api("/auth/me/");
export const login = (username, password) =>
  api("/auth/login/", { method: "POST", body: { username, password } });
export const logout = () => api("/auth/logout/", { method: "POST" });
export const signUp = (form) => api("/auth/signup/", { method: "POST", body: form });

export const updateAccount = (form) => api("/auth/profile/", { method: "POST", body: form });
export const changePassword = (form) => api("/auth/password/", { method: "POST", body: form });
export const requestPasswordReset = (email) =>
  api("/auth/password-reset/", { method: "POST", body: { email } });