import useDashboard from "../../hooks/useDashboard";
import { 
  Activity, 
  Database, 
  Brain, 
  ShieldAlert, 
  Workflow,
  ArrowRight
} from "lucide-react";
import { Link } from "react-router-dom";

export default function DashboardPage() {
  const { dashboardData, loading } = useDashboard();

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="rounded-lg border border-slate-200 bg-white p-12 text-center text-[14px] text-slate-500 shadow-[0_12px_34px_rgba(15,23,42,0.04)]">
          Loading Workspace Overview...
        </div>
      </div>
    );
  }

  const stats = dashboardData?.stats || { total_models: 0, total_runs: 0, open_incidents: 0 };
  const user = dashboardData?.user;

  return (
    <div className="space-y-5">
      {/* HEADER */}
      <section className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-[0_12px_34px_rgba(15,23,42,0.04)]">
        <div className="border-b border-slate-200 px-6 py-5">
          <h1 className="text-[30px] font-semibold leading-tight text-slate-950">Overview</h1>
          <p className="mt-2 max-w-[720px] text-[14px] leading-6 text-slate-500">
            Welcome back, {user?.email}. Here is the high-level health and activity summary of your machine learning infrastructure.
          </p>
        </div>
      </section>

      {/* KPI CARDS */}
      <div className="grid grid-cols-3 gap-5">
        <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-[0_12px_34px_rgba(15,23,42,0.04)] transition hover:shadow-[0_16px_42px_rgba(15,23,42,0.07)]">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-md border border-blue-100 bg-blue-50 text-blue-600">
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
        
        <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-[0_12px_34px_rgba(15,23,42,0.04)] transition hover:shadow-[0_16px_42px_rgba(15,23,42,0.07)]">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-md border border-indigo-100 bg-indigo-50 text-indigo-600">
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

        <div className={`rounded-lg border ${stats.open_incidents > 0 ? 'border-red-200' : 'border-slate-200'} bg-white p-6 shadow-[0_12px_34px_rgba(15,23,42,0.04)] transition hover:shadow-[0_16px_42px_rgba(15,23,42,0.07)]`}>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className={`flex h-10 w-10 items-center justify-center rounded-md border ${stats.open_incidents > 0 ? 'border-red-100 bg-red-50 text-red-600' : 'border-slate-200 bg-slate-50 text-slate-400'}`}>
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
      <div className="overflow-hidden rounded-lg border border-slate-200 bg-white p-6 shadow-[0_12px_34px_rgba(15,23,42,0.04)]">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-6">
            <div className={`flex h-14 w-14 items-center justify-center rounded-md ${stats.open_incidents === 0 ? 'bg-green-50 text-green-600 border border-green-100' : 'bg-red-50 text-red-600 border border-red-100'}`}>
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
            <Link to="/data-quality" className="flex items-center gap-2 rounded-md border border-slate-200 bg-white px-4 py-2 text-[13px] font-semibold text-slate-600 transition hover:bg-slate-50">
              <Database size={16} /> Data Quality
            </Link>
            <Link to="/drift" className="flex items-center gap-2 rounded-md border border-slate-200 bg-white px-4 py-2 text-[13px] font-semibold text-slate-600 transition hover:bg-slate-50">
              <Activity size={16} /> Drift Analytics
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
