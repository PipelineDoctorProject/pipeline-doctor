import { Navigate } from "react-router-dom";
import useAuthStore from "../store/authStore";
import LoadingScreen from "../components/common/LoadingScreen";

export default function TenantRoute({ children }) {

  const workspace = useAuthStore(
    (state) => state.workspace
  );

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

  if (!workspace?.tenant_id) {
    return <Navigate to="/onboarding" replace />;
  }

  return children;
}