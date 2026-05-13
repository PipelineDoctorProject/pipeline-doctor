import { useEffect, useState } from "react";
import { Activity, ShieldAlert, AlertTriangle, Info, BarChart2 } from "lucide-react";
import { getDriftFindings } from "../../store/driftStore";

export default function DriftPage() {
  const [findings, setFindings] = useState([]);
  const [loading, setLoading] = useState(true);

  // ==========================================
  // LOAD DRIFT FINDINGS
  // ==========================================
  const loadFindings = async () => {
    try {
      setLoading(true);
      const data = await getDriftFindings();
      setFindings(data);
    } catch (err) {
      console.log(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFindings();
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
        <span className="capitalize">{severity || "Low"}</span>
      </div>
    );
  };

  return (
    <div className="space-y-8">
      {/* HEADER */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-[34px] font-semibold tracking-[-0.04em] text-[#111827]">
            Drift Detection
          </h1>
          <p className="mt-2 max-w-[720px] text-[15px] leading-7 text-gray-500">
            Monitor feature and target drift across your machine learning models. 
            Analyze changes in data distributions using PSI and KS metrics compared to your MLflow baselines.
          </p>
        </div>
        <button
          onClick={loadFindings}
          className="flex items-center gap-3 rounded-2xl border border-black/[0.05] bg-white px-5 py-3 text-[13px] font-medium text-[#111827] shadow-sm transition hover:bg-[#f7f8fb]"
        >
          <Activity size={16} />
          Refresh Analysis
        </button>
      </div>

      {/* STATS ROW */}
      <div className="grid grid-cols-3 gap-6">
        <div className="rounded-3xl border border-black/[0.05] bg-white p-6 shadow-[0_20px_50px_rgba(15,23,42,0.03)]">
          <div className="flex items-center gap-3 mb-3">
            <div className="h-10 w-10 rounded-full bg-red-50 flex items-center justify-center text-red-600">
              <ShieldAlert size={18} />
            </div>
            <span className="text-[13px] font-medium text-gray-500 uppercase tracking-wider">Features Drifting</span>
          </div>
          <p className="text-3xl font-semibold text-[#111827]">{findings.filter(f => f.drift_detected).length}</p>
        </div>
        
        <div className="col-span-2 rounded-3xl border border-black/[0.05] bg-white p-6 shadow-[0_20px_50px_rgba(15,23,42,0.03)] flex flex-col justify-center items-center text-gray-400">
          <BarChart2 size={32} className="mb-2 opacity-50" />
          <p className="text-sm font-medium">Global Drift Trend Chart</p>
          <p className="text-xs mt-1">(Metrics visualization will populate here after sufficient data collection)</p>
        </div>
      </div>

      {/* LOADING STATE */}
      {loading && (
        <div className="rounded-3xl border border-black/[0.05] bg-white p-12 text-center text-[14px] text-gray-500 shadow-[0_20px_50px_rgba(15,23,42,0.03)]">
          Loading Drift Analysis...
        </div>
      )}

      {/* EMPTY STATE */}
      {!loading && findings.length === 0 && (
        <div className="rounded-3xl border border-dashed border-black/[0.08] bg-white p-16 text-center shadow-[0_20px_50px_rgba(15,23,42,0.03)]">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-blue-50 mb-4 border border-blue-100">
            <Activity size={28} className="text-blue-500" />
          </div>
          <h3 className="text-[18px] font-semibold text-[#111827]">
            No Drift Detected
          </h3>
          <p className="mt-2 text-[14px] text-gray-500 max-w-sm mx-auto">
            Your models are behaving as expected compared to their baselines. Analysis will appear here when shifts occur.
          </p>
        </div>
      )}

      {/* DATA TABLE */}
      {!loading && findings.length > 0 && (
        <div className="overflow-hidden rounded-3xl border border-black/[0.05] bg-white shadow-[0_20px_50px_rgba(15,23,42,0.03)]">
          <table className="w-full text-left text-[14px]">
            <thead className="bg-[#f7f8fb] text-[12px] font-medium uppercase tracking-[0.1em] text-gray-500">
              <tr>
                <th className="px-6 py-5">Severity</th>
                <th className="px-6 py-5">Feature</th>
                <th className="px-6 py-5">Drift Score</th>
                <th className="px-6 py-5">PSI Score</th>
                <th className="px-6 py-5">KS Stats</th>
                <th className="px-6 py-5 text-right">Run ID</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-black/[0.04]">
              {findings.map((finding) => (
                <tr
                  key={finding.id}
                  className="transition hover:bg-[#f7f8fb]/50 group"
                >
                  <td className="px-6 py-5">
                    {renderSeverityBadge(finding.severity)}
                  </td>
                  <td className="px-6 py-5">
                    <span className="font-mono text-[13px] bg-gray-50 px-2 py-1 rounded text-gray-700 border border-gray-100">
                      {finding.feature_name}
                    </span>
                  </td>
                  <td className="px-6 py-5">
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                        <div 
                          className={`h-full ${finding.drift_score > 0.5 ? 'bg-red-500' : 'bg-green-500'}`} 
                          style={{width: `${Math.min(finding.drift_score * 100, 100)}%`}}
                        ></div>
                      </div>
                      <span className="text-xs font-medium text-gray-600">{finding.drift_score.toFixed(3)}</span>
                    </div>
                  </td>
                  <td className="px-6 py-5">
                    <span className="text-gray-600">
                      {finding.psi_score !== null ? finding.psi_score.toFixed(4) : "N/A"}
                    </span>
                  </td>
                  <td className="px-6 py-5">
                    <div className="flex flex-col text-xs">
                      <span className="text-gray-600">
                        <span className="text-gray-400">Score:</span> {finding.ks_score !== null ? finding.ks_score.toFixed(4) : "N/A"}
                      </span>
                      <span className="text-gray-600">
                        <span className="text-gray-400">p-value:</span> {finding.ks_pvalue !== null ? finding.ks_pvalue.toFixed(4) : "N/A"}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-5 text-right">
                    <a href={`/pipelines?run=${finding.run_id}`} className="text-blue-600 hover:underline">
                      #{finding.run_id}
                    </a>
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
