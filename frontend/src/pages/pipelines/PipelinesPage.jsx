import { useEffect, useState } from "react";
import { Workflow, CheckCircle2, XCircle, AlertCircle, Clock, Download } from "lucide-react";
import { getPipelineRuns } from "../../store/pipelineStore";

export default function PipelinesPage() {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(null);

  // ==========================================
  // LOAD PIPELINE RUNS
  // ==========================================
  const loadRuns = async () => {
    try {
      setLoading(true);
      const data = await getPipelineRuns();
      setRuns(data);
    } catch (err) {
      console.log(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRuns();
  }, []);

  // ==========================================
  // DOWNLOAD CLEANED DATA
  // ==========================================
  const downloadCleaned = async (runId) => {
    try {
      setDownloading(runId);
      const response = await fetch(
        `http://localhost:8000/runs/${runId}/download-cleaned`,
        {
          // Use credentials: include so cookies are sent automatically
          credentials: "include",
        }
      );

      if (!response.ok) {
        const err = await response.json();
        alert(`Download failed: ${err.detail}`);
        return;
      }

      // Trigger browser download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `cleaned_run_${runId}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error(err);
      alert("Download failed. Check that the backend is running.");
    } finally {
      setDownloading(null);
    }
  };

  // Format Status Badge
  const renderStatusBadge = (status) => {
    const statusConfig = {
      success: {
        bg: "bg-green-50",
        text: "text-green-700",
        border: "border-green-200",
        icon: <CheckCircle2 size={14} className="mr-1.5" />,
      },
      failed: {
        bg: "bg-red-50",
        text: "text-red-700",
        border: "border-red-200",
        icon: <XCircle size={14} className="mr-1.5" />,
      },
      running: {
        bg: "bg-blue-50",
        text: "text-blue-700",
        border: "border-blue-200",
        icon: <Clock size={14} className="mr-1.5 animate-pulse" />,
      },
      default: {
        bg: "bg-gray-100",
        text: "text-gray-700",
        border: "border-gray-200",
        icon: <AlertCircle size={14} className="mr-1.5" />,
      },
    };

    const config = statusConfig[status?.toLowerCase()] || statusConfig.default;

    return (
      <div
        className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border ${config.bg} ${config.text} ${config.border}`}
      >
        {config.icon}
        <span className="capitalize">{status}</span>
      </div>
    );
  };

  return (
    <div className="space-y-8">
      {/* HEADER */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-[34px] font-semibold tracking-[-0.04em] text-[#111827]">
            Pipeline Runs
          </h1>
          <p className="mt-2 max-w-[720px] text-[15px] leading-7 text-gray-500">
            Monitor historical and active inference pipelines. Track performance,
            drift evaluations, and quality checks across your deployed models.
          </p>
        </div>
        <button
          onClick={loadRuns}
          className="flex items-center gap-3 rounded-2xl border border-black/[0.05] bg-white px-5 py-3 text-[13px] font-medium text-[#111827] shadow-sm transition hover:bg-[#f7f8fb]"
        >
          <Workflow size={16} />
          Refresh Runs
        </button>
      </div>

      {/* LOADING STATE */}
      {loading && (
        <div className="rounded-3xl border border-black/[0.05] bg-white p-12 text-center text-[14px] text-gray-500 shadow-[0_20px_50px_rgba(15,23,42,0.03)]">
          Loading Pipeline Runs...
        </div>
      )}

      {/* EMPTY STATE */}
      {!loading && runs.length === 0 && (
        <div className="rounded-3xl border border-dashed border-black/[0.08] bg-white p-16 text-center shadow-[0_20px_50px_rgba(15,23,42,0.03)]">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-gray-50 mb-4">
            <Workflow size={28} className="text-gray-400" />
          </div>
          <h3 className="text-[18px] font-semibold text-[#111827]">
            No Pipeline Runs Found
          </h3>
          <p className="mt-2 text-[14px] text-gray-500 max-w-sm mx-auto">
            Inference pipelines will automatically appear here once data begins flowing through your registered models.
          </p>
        </div>
      )}

      {/* DATA TABLE */}
      {!loading && runs.length > 0 && (
        <div className="overflow-hidden rounded-3xl border border-black/[0.05] bg-white shadow-[0_20px_50px_rgba(15,23,42,0.03)]">
          <table className="w-full text-left text-[14px]">
            <thead className="bg-[#f7f8fb] text-[12px] font-medium uppercase tracking-[0.1em] text-gray-500">
              <tr>
                <th className="px-6 py-5">Run ID</th>
                <th className="px-6 py-5">Model</th>
                <th className="px-6 py-5">Status</th>
                <th className="px-6 py-5">Baseline Version</th>
                <th className="px-6 py-5">Schema Status</th>
                <th className="px-6 py-5">Started At</th>
                <th className="px-6 py-5 text-right">Cleaned Data</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-black/[0.04]">
              {runs.map((run) => (
                <tr
                  key={run.id}
                  className="transition hover:bg-[#f7f8fb]/50 group"
                >
                  <td className="px-6 py-5 font-medium text-[#111827]">
                    #{run.id}
                  </td>
                  <td className="px-6 py-5">
                    <div className="flex flex-col">
                      <span className="font-medium text-[#111827]">
                        {run.model?.name || `Model ${run.model_id}`}
                      </span>
                      <span className="text-xs text-gray-500">
                        {run.model?.version ? `v${run.model.version}` : 'Unknown Version'}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-5">
                    {renderStatusBadge(run.status)}
                  </td>
                  <td className="px-6 py-5 text-gray-600">
                    v{run.baseline_version}
                  </td>
                  <td className="px-6 py-5">
                    {run.schema_changed ? (
                      <span className="text-orange-600 font-medium text-xs bg-orange-50 px-2 py-1 rounded-full">Modified</span>
                    ) : (
                      <span className="text-gray-500 text-xs">Unchanged</span>
                    )}
                  </td>
                  <td className="px-6 py-5 text-gray-500">
                    {new Date(run.created_at).toLocaleString()}
                  </td>
                  <td className="px-6 py-5 text-right">
                    {run.status === "success" ? (
                      <button
                        onClick={() => downloadCleaned(run.id)}
                        disabled={downloading === run.id}
                        className="inline-flex items-center gap-1.5 rounded-xl border border-black/[0.05] bg-white px-3 py-1.5 text-xs font-medium text-gray-600 shadow-sm transition hover:bg-green-50 hover:text-green-700 hover:border-green-200 disabled:opacity-50"
                      >
                        <Download size={12} />
                        {downloading === run.id ? "Downloading..." : "Download CSV"}
                      </button>
                    ) : (
                      <span className="text-xs text-gray-400">N/A</span>
                    )}
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
