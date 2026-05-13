import useDashboard from "../../hooks/useDashboard";
import { 
  Activity, 
  Database, 
  Brain, 
  ShieldAlert, 
  Workflow,
  ArrowRight,
  ShieldCheck
} from "lucide-react";
import { Link } from "react-router-dom";

export default function DashboardPage() {
  const { dashboardData, loading } = useDashboard();

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="rounded-3xl border border-black/[0.05] bg-white p-12 text-center text-[14px] text-gray-500 shadow-[0_20px_50px_rgba(15,23,42,0.03)]">
          Loading Workspace Overview...
        </div>
      </div>
    );
  }

  const stats = dashboardData?.stats || { total_models: 0, total_runs: 0, open_incidents: 0 };
  const user = dashboardData?.user;
  const workspace = dashboardData?.workspace;

  return (
    <div className="space-y-8">
      {/* HEADER */}
      <div className="flex items-start justify-between">
        <div>
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-black/[0.05] bg-white px-3 py-1 text-[10px] font-medium uppercase tracking-[0.2em] text-gray-500 shadow-sm">
            <ShieldCheck size={12} className="text-green-600" />
            Active Workspace
          </div>
          <h1 className="text-[34px] font-semibold tracking-[-0.04em] text-[#111827]">
            Overview: {workspace?.workspace_name}
          </h1>
          <p className="mt-2 max-w-[720px] text-[15px] leading-7 text-gray-500">
            Welcome back, {user?.email}. Here is the high-level health and activity summary of your machine learning infrastructure.
          </p>
        </div>
      </div>

      {/* KPI CARDS */}
      <div className="grid grid-cols-3 gap-6">
        <div className="rounded-3xl border border-black/[0.05] bg-white p-6 shadow-[0_20px_50px_rgba(15,23,42,0.03)] transition hover:shadow-[0_20px_50px_rgba(15,23,42,0.06)]">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-full bg-blue-50 flex items-center justify-center text-blue-600">
                <Brain size={18} />
              </div>
              <span className="text-[13px] font-medium text-gray-500 uppercase tracking-wider">Connected Models</span>
            </div>
          </div>
          <div className="flex items-end justify-between">
            <p className="text-4xl font-semibold tracking-tight text-[#111827]">{stats.total_models}</p>
            <Link to="/models" className="flex items-center gap-1 text-xs font-medium text-blue-600 hover:text-blue-700 hover:underline">
              View All <ArrowRight size={12} />
            </Link>
          </div>
        </div>
        
        <div className="rounded-3xl border border-black/[0.05] bg-white p-6 shadow-[0_20px_50px_rgba(15,23,42,0.03)] transition hover:shadow-[0_20px_50px_rgba(15,23,42,0.06)]">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-full bg-indigo-50 flex items-center justify-center text-indigo-600">
                <Workflow size={18} />
              </div>
              <span className="text-[13px] font-medium text-gray-500 uppercase tracking-wider">Pipeline Runs</span>
            </div>
          </div>
          <div className="flex items-end justify-between">
            <p className="text-4xl font-semibold tracking-tight text-[#111827]">{stats.total_runs}</p>
            <Link to="/pipelines" className="flex items-center gap-1 text-xs font-medium text-indigo-600 hover:text-indigo-700 hover:underline">
              View History <ArrowRight size={12} />
            </Link>
          </div>
        </div>

        <div className={`rounded-3xl border ${stats.open_incidents > 0 ? 'border-red-200' : 'border-black/[0.05]'} bg-white p-6 shadow-[0_20px_50px_rgba(15,23,42,0.03)] transition hover:shadow-[0_20px_50px_rgba(15,23,42,0.06)]`}>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className={`h-10 w-10 rounded-full flex items-center justify-center ${stats.open_incidents > 0 ? 'bg-red-50 text-red-600' : 'bg-gray-50 text-gray-400'}`}>
                <ShieldAlert size={18} />
              </div>
              <span className="text-[13px] font-medium text-gray-500 uppercase tracking-wider">Open Incidents</span>
            </div>
            {stats.open_incidents > 0 && (
              <span className="flex h-2.5 w-2.5 rounded-full bg-red-500 animate-pulse"></span>
            )}
          </div>
          <div className="flex items-end justify-between">
            <p className={`text-4xl font-semibold tracking-tight ${stats.open_incidents > 0 ? 'text-red-600' : 'text-[#111827]'}`}>
              {stats.open_incidents}
            </p>
            <Link to="/incidents" className="flex items-center gap-1 text-xs font-medium text-gray-600 hover:text-gray-900 hover:underline">
              Resolve <ArrowRight size={12} />
            </Link>
          </div>
        </div>
      </div>

      {/* SYSTEM HEALTH BANNER */}
      <div className="relative overflow-hidden rounded-[24px] border border-black/[0.05] bg-[#f8fafc] p-8 mt-8">
        <div className="absolute top-[-20%] right-[-10%] h-[380px] w-[380px] rounded-full bg-[#3563ff]/[0.04] blur-[100px]" />
        <div className="absolute bottom-[-30%] left-[-10%] h-[300px] w-[300px] rounded-full bg-[#7c3aed]/[0.03] blur-[100px]" />
        
        <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-6">
            <div className={`h-16 w-16 rounded-2xl flex items-center justify-center shadow-sm ${stats.open_incidents === 0 ? 'bg-green-50 text-green-600 border border-green-100' : 'bg-red-50 text-red-600 border border-red-100'}`}>
              <Activity size={28} />
            </div>
            <div>
              <h3 className="text-[20px] font-semibold text-[#111827]">
                {stats.open_incidents === 0 ? "All Systems Operational" : "Attention Required"}
              </h3>
              <p className="mt-1 text-[14px] text-gray-500 max-w-md">
                {stats.open_incidents === 0 
                  ? "Your machine learning infrastructure is healthy. Data quality, schema validation, and drift metrics are within acceptable thresholds." 
                  : "There are active incidents requiring your attention. Please check the incident management console."}
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <Link to="/data-quality" className="flex items-center gap-2 rounded-xl border border-black/[0.05] bg-white px-4 py-2 text-[13px] font-medium text-gray-600 transition hover:bg-gray-50">
              <Database size={16} /> Data Quality
            </Link>
            <Link to="/drift" className="flex items-center gap-2 rounded-xl border border-black/[0.05] bg-white px-4 py-2 text-[13px] font-medium text-gray-600 transition hover:bg-gray-50">
              <Activity size={16} /> Drift Analytics
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}