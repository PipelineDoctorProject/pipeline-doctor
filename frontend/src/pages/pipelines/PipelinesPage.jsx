import { useEffect, useState } from "react";
import { Workflow, CheckCircle2, XCircle, AlertCircle, Clock, Download } from "lucide-react";
import { useSearchParams } from "react-router-dom";
import { getPipelineRuns } from "../../store/pipelineStore";

export default function PipelinesPage() {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(null);
  const [searchParams] = useSearchParams();
  const highlightedRunId = searchParams.get("run");

  // ==========================================
  // LOAD PIPELINE RUNS
  // ==========================================
  const loadRuns = async () => {
    try {
      setLoading(true);
      const data = await getPipelineRuns();
      setRuns(data || []);
    } catch (err) {
      console.log(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
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
    <div className="space-y-5">
      {/* HEADER */}
      <section className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-[0_12px_34px_rgba(15,23,42,0.04)]">
        <div className="flex flex-col gap-5 border-b border-slate-200 px-6 py-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <h1 className="text-[30px] font-semibold leading-tight text-slate-950">
              Pipeline Runs
            </h1>
            <p className="mt-2 max-w-[720px] text-[14px] leading-6 text-slate-500">
              Monitor historical and active inference pipelines. Track performance,
              drift evaluations, and quality checks across your deployed models.
            </p>
          </div>
          <button
            onClick={loadRuns}
            className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-slate-950 px-4 text-[13px] font-semibold text-white transition hover:bg-slate-800"
          >
            <Workflow size={16} />
            Refresh Runs
          </button>
        </div>
      </section>

      {/* LOADING STATE */}
      {loading && (
        <div className="rounded-lg border border-slate-200 bg-white p-12 text-center text-[14px] text-slate-500 shadow-[0_12px_34px_rgba(15,23,42,0.04)]">
          Loading Pipeline Runs...
        </div>
      )}

      {/* EMPTY STATE */}
      {!loading && runs.length === 0 && (
        <div className="rounded-lg border border-dashed border-slate-200 bg-white p-16 text-center shadow-[0_12px_34px_rgba(15,23,42,0.04)]">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-md border border-slate-200 bg-slate-50">
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
        <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-[0_12px_34px_rgba(15,23,42,0.04)]">
          <table className="w-full text-left text-[14px]">
            <thead className="bg-slate-50 text-[12px] font-medium uppercase tracking-[0.1em] text-slate-500">
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
            <tbody className="divide-y divide-slate-200">
              {runs.map((run) => (
                <tr
                  key={run.id}
                  className={`group transition ${
                    String(run.id) === highlightedRunId
                      ? "bg-blue-50/60 shadow-[inset_4px_0_0_#2563eb]"
                      : "hover:bg-slate-50/70"
                  }`}
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
                      <span className="rounded-md border border-orange-200 bg-orange-50 px-2.5 py-1 text-xs font-semibold text-orange-700">Modified</span>
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
                        className="inline-flex items-center gap-1.5 rounded-md border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 transition hover:border-green-200 hover:bg-green-50 hover:text-green-700 disabled:opacity-50"
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
