import useAuthStore from "../store/authStore";

export default function useDashboard() {
  const dashboardData = useAuthStore((state) => state.dashboardData);
  const checkingAuth = useAuthStore((state) => state.checkingAuth);

  return {
    dashboardData,
    loading: checkingAuth,
  };
}
