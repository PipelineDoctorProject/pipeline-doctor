import { useEffect, useState } from "react";
import { AlertTriangle, AlertCircle, Info, ShieldAlert } from "lucide-react";
import { getIncidents } from "../../store/incidentStore";

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);

  // ==========================================
  // LOAD INCIDENTS
  // ==========================================
  const loadIncidents = async () => {
    try {
      setLoading(true);
      const data = await getIncidents();
      setIncidents(data);
    } catch (err) {
      console.log(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadIncidents();
  }, []);

  // Format Severity Badge
  const renderSeverityBadge = (severity) => {
    const config = {
      critical: {
        bg: "bg-red-50",
        text: "text-red-700",
        border: "border-red-200",
        icon: <ShieldAlert size={14} className="mr-1.5" />,
      },
      high: {
        bg: "bg-orange-50",
        text: "text-orange-700",
        border: "border-orange-200",
        icon: <AlertTriangle size={14} className="mr-1.5" />,
      },
      medium: {
        bg: "bg-yellow-50",
        text: "text-yellow-700",
        border: "border-yellow-200",
        icon: <AlertCircle size={14} className="mr-1.5" />,
      },
      low: {
        bg: "bg-blue-50",
        text: "text-blue-700",
        border: "border-blue-200",
        icon: <Info size={14} className="mr-1.5" />,
      },
      default: {
        bg: "bg-gray-100",
        text: "text-gray-700",
        border: "border-gray-200",
        icon: <Info size={14} className="mr-1.5" />,
      },
    };

    const style = config[severity?.toLowerCase()] || config.default;

    return (
      <div
        className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border ${style.bg} ${style.text} ${style.border}`}
      >
        {style.icon}
        <span className="capitalize">{severity || "Unknown"}</span>
      </div>
    );
  };

  // Format Status Badge
  const renderStatusBadge = (status) => {
    const isResolved = status?.toLowerCase() === "resolved" || status?.toLowerCase() === "closed";
    
    return (
      <span
        className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
          isResolved
            ? "bg-gray-100 text-gray-600 border border-gray-200"
            : "bg-red-50 text-red-600 border border-red-100"
        }`}
      >
        <span className={`mr-1.5 h-1.5 w-1.5 rounded-full ${isResolved ? "bg-gray-400" : "bg-red-500 animate-pulse"}`}></span>
        {status || "Open"}
      </span>
    );
  };

  return (
    <div className="space-y-8">
      {/* HEADER */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-[34px] font-semibold tracking-[-0.04em] text-[#111827]">
            Incidents
          </h1>
          <p className="mt-2 max-w-[720px] text-[15px] leading-7 text-gray-500">
            Triage and resolve active alerts across your ML infrastructure. 
            Incidents are automatically created when pipelines detect severe drift, data quality failures, or schema changes.
          </p>
        </div>
        <button
          onClick={loadIncidents}
          className="flex items-center gap-3 rounded-2xl border border-black/[0.05] bg-white px-5 py-3 text-[13px] font-medium text-[#111827] shadow-sm transition hover:bg-[#f7f8fb]"
        >
          <AlertTriangle size={16} />
          Refresh Incidents
        </button>
      </div>

      {/* LOADING STATE */}
      {loading && (
        <div className="rounded-3xl border border-black/[0.05] bg-white p-12 text-center text-[14px] text-gray-500 shadow-[0_20px_50px_rgba(15,23,42,0.03)]">
          Loading Incidents...
        </div>
      )}

      {/* EMPTY STATE */}
      {!loading && incidents.length === 0 && (
        <div className="rounded-3xl border border-dashed border-black/[0.08] bg-white p-16 text-center shadow-[0_20px_50px_rgba(15,23,42,0.03)]">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-green-50 mb-4 border border-green-100">
            <ShieldAlert size={28} className="text-green-600" />
          </div>
          <h3 className="text-[18px] font-semibold text-[#111827]">
            All Clear
          </h3>
          <p className="mt-2 text-[14px] text-gray-500 max-w-sm mx-auto">
            Your ML infrastructure is healthy. No active incidents or alerts require your attention.
          </p>
        </div>
      )}

      {/* DATA TABLE */}
      {!loading && incidents.length > 0 && (
        <div className="overflow-hidden rounded-3xl border border-black/[0.05] bg-white shadow-[0_20px_50px_rgba(15,23,42,0.03)]">
          <table className="w-full text-left text-[14px]">
            <thead className="bg-[#f7f8fb] text-[12px] font-medium uppercase tracking-[0.1em] text-gray-500">
              <tr>
                <th className="px-6 py-5">Severity</th>
                <th className="px-6 py-5">Title & Context</th>
                <th className="px-6 py-5">Type</th>
                <th className="px-6 py-5">Status</th>
                <th className="px-6 py-5">Run ID</th>
                <th className="px-6 py-5 text-right">Detected At</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-black/[0.04]">
              {incidents.map((incident) => (
                <tr
                  key={incident.id}
                  className="transition hover:bg-[#f7f8fb]/50 group"
                >
                  <td className="px-6 py-5">
                    {renderSeverityBadge(incident.severity)}
                  </td>
                  <td className="px-6 py-5">
                    <div className="flex flex-col">
                      <span className="font-medium text-[#111827]">
                        {incident.title}
                      </span>
                      <span className="text-xs text-gray-500 max-w-xs truncate" title={incident.description}>
                        {incident.description}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-5">
                    <span className="inline-block bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded font-mono">
                      {incident.failure_type}
                    </span>
                  </td>
                  <td className="px-6 py-5">
                    {renderStatusBadge(incident.status)}
                  </td>
                  <td className="px-6 py-5 text-gray-600">
                    <a href={`/pipelines?run=${incident.run_id}`} className="hover:text-blue-600 hover:underline">
                      #{incident.run_id}
                    </a>
                  </td>
                  <td className="px-6 py-5 text-right text-gray-500">
                    {new Date(incident.created_at).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
