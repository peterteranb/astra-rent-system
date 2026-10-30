import { Navigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function ProtectedRoute({ roles, children }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (!user) return <Navigate to="/login" replace />;
  // El administrador puede todo (ENT-13)
  if (roles && user.role !== "administrador" && !roles.includes(user.role)) {
    return <Navigate to="/403" replace />;
  }
  return children;
}
