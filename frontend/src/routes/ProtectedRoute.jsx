import { Navigate } from "react-router-dom";
import useAuthStore from "../store/authStore";
import LoadingScreen from "../components/common/LoadingScreen";

export default function ProtectedRoute({ children }) {

  const isAuthenticated = useAuthStore(
    (state) => state.isAuthenticated
  );

  const checkingAuth = useAuthStore(
    (state) => state.checkingAuth
  );

  if (checkingAuth) {
    return <LoadingScreen />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
}