import { useEffect, useState } from "react";

import useAuthStore from "../store/authStore";

export default function useDashboard() {

  const getMe = useAuthStore((state) => state.me);

  const [dashboardData, setDashboardData] = useState(null);

  const [loading, setLoading] = useState(true);

  useEffect(() => {

    const loadDashboard = async () => {

      try {

        const data = await getMe();

        setDashboardData(data);

      } catch (err) {

        console.log(err);

      } finally {

        setLoading(false);
      }
    };

    loadDashboard();

  }, []);

  return {
    dashboardData,
    loading,
  };
}