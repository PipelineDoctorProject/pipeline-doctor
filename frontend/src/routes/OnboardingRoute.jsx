import { Navigate } from "react-router-dom";
import useAuthStore from "../store/authStore";

export default function OnboardingRoute({ children }) {

  const isAuthenticated = useAuthStore(
    (state) => state.isAuthenticated
  );

  const checkingAuth = useAuthStore(
    (state) => state.checkingAuth
  );

  if (checkingAuth) {
    return <div>Loading...</div>;
  }

  // not logged in
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
}