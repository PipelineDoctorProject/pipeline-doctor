import useDashboard from "../../hooks/useDashboard";

export default function DashboardPage() {

  const {
    dashboardData,
    loading,
  } = useDashboard();

  if (loading) {
    return <div>Loading...</div>;
  }

  return (

    <div>

      <h1 className="text-4xl font-semibold text-[#111827]">

        Welcome back
      </h1>

      <p className="mt-2 text-gray-500">

        Workspace:
        {" "}
        {dashboardData?.workspace?.workspace_name}
      </p>
    </div>
  );
}