import { Navigate } from "react-router-dom";
import useAuthStore from "../store/authStore";

export default function PublicRoute({ children }) {

  const isAuthenticated = useAuthStore(
    (state) => state.isAuthenticated
  );

  const checkingAuth = useAuthStore(
    (state) => state.checkingAuth
  );

  if (checkingAuth) {
    return <div>Loading...</div>;
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
}