import { useEffect, useState } from "react";

import useAuthStore from "../store/authStore";

export default function DashboardPage() {
  const getMe = useAuthStore((state) => state.me);

  const [workspaceName, setWorkspaceName] = useState("");

  const [userEmail, setUserEmail] = useState("");

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadDashboard = async () => {
      try {
        const data = await getMe();

        console.log(data);

        setWorkspaceName(data.workspace.workspace_name);

        setUserEmail(data.user.email);
      } catch (err) {
        console.log(err);
      } finally {
        setLoading(false);
      }
    };

    loadDashboard();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-black text-white">
        Loading Dashboard...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 p-10">
      <h1 className="text-4xl font-bold mb-4">PipelineDoctor Dashboard</h1>

      <div className="bg-white p-6 rounded-xl shadow-md max-w-xl">
        <p className="text-gray-500 mb-2">Workspace Name</p>

        <h2 className="text-2xl font-semibold mb-6">{workspaceName}</h2>

        <p className="text-gray-500 mb-2">Logged In User</p>

        <p className="text-lg">{userEmail}</p>
        
      </div>
    </div>
  );
}
