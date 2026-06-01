import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  CheckCircle2,
  Clock3,
  Play,
  RefreshCw,
  ShieldAlert,
  Wrench,
  XCircle,
} from "lucide-react";
import toast from "react-hot-toast";

import useAuthStore from "../../store/authStore";
import {
  approveRemediationForIncident,
  getRemediationContext,
  getRemediationRunLogs,
  getRemediationRunsForIncident,
  promoteRemediationCandidate,
  rejectRemediationCandidate,
  rejectRemediationRun,
} from "../../store/remediationStore";

const RUN_STATUS_STYLES = {
  queued: "border-indigo-200 bg-indigo-50 text-indigo-700",
  approved: "border-sky-200 bg-sky-50 text-sky-700",
  running: "border-amber-200 bg-amber-50 text-amber-700",
  completed: "border-emerald-200 bg-emerald-50 text-emerald-700",
  pending_promotion: "border-violet-200 bg-violet-50 text-violet-700",
  promoted: "border-emerald-200 bg-emerald-100 text-emerald-800",
  promotion_rejected: "border-rose-200 bg-rose-50 text-rose-700",
  failed: "border-red-200 bg-red-50 text-red-700",
  blocked: "border-orange-200 bg-orange-50 text-orange-700",
  rejected: "border-slate-200 bg-slate-100 text-slate-700",
  cancel_requested: "border-rose-200 bg-rose-50 text-rose-700",
  canceled: "border-slate-300 bg-slate-100 text-slate-700",
  default: "border-slate-200 bg-slate-50 text-slate-700",
};

function formatDate(value) {
  if (!value) return "Not available";

  return new Date(value).toLocaleString(undefined, {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function humanize(value) {
  return String(value || "unknown")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function StatusBadge({ status }) {
  const normalized = String(status || "").toLowerCase();
  const className = RUN_STATUS_STYLES[normalized] || RUN_STATUS_STYLES.default;

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide ${className}`}
    >
      {humanize(normalized)}
    </span>
  );
}

function SummaryCard({ label, value, detail, icon: Icon, tone = "slate" }) {
  const toneClasses = {
    slate: "border-slate-200 bg-slate-50",
    blue: "border-blue-100 bg-blue-50",
    violet: "border-violet-100 bg-violet-50",
    amber: "border-amber-100 bg-amber-50",
  };
  const iconClasses = {
    slate: "bg-slate-200 text-slate-700",
    blue: "bg-blue-100 text-blue-700",
    violet: "bg-violet-100 text-violet-700",
    amber: "bg-amber-100 text-amber-700",
  };

  return (
    <div className={`rounded-lg border p-4 ${toneClasses[tone] || toneClasses.slate}`}>
      <div className="flex items-center gap-2">
        <div
          className={`flex h-7 w-7 items-center justify-center rounded-md ${iconClasses[tone] || iconClasses.slate}`}
        >
          <Icon size={14} />
        </div>
        <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">
          {label}
        </p>
      </div>
      <p className="mt-3 text-[15px] font-semibold leading-6 text-slate-950">{value}</p>
      {detail && <p className="mt-1 text-[12px] leading-5 text-slate-500">{detail}</p>}
    </div>
  );
}

function deriveRemediationSummary(incident) {
  if (incident?.remediation) {
    return incident.remediation;
  }

  if (!incident?.final_report) {
    return null;
  }

  return {
    recommended_action:
      incident.final_report.recommended_action ||
      incident.final_report.action_taken ||
      "Review the final report before executing remediation.",
    action_type: incident.final_report.action_type,
    action_mode: incident.final_report.action_mode,
    requires_approval: Boolean(incident.final_report.requires_approval),
    allowed_to_execute: !incident.final_report.manual_action_required,
    manual_only: Boolean(incident.final_report.manual_action_required),
    reason:
      incident.final_report.timeline_summary ||
      incident.final_report.action_taken ||
      "Refer to the final incident report for lifecycle details.",
  };
}

export default function IncidentRemediationPanel({
  incident,
  onRemediationChanged,
}) {
  const user = useAuthStore((state) => state.user);
  const isAdmin = user?.role === "admin";
  const remediation = deriveRemediationSummary(incident);

  const [context, setContext] = useState(null);
  const [runs, setRuns] = useState([]);
  const [logs, setLogs] = useState([]);
  const [selectedRunId, setSelectedRunId] = useState(null);
  const [targetColumn, setTargetColumn] = useState("");
  const [loadingContext, setLoadingContext] = useState(true);
  const [loadingRuns, setLoadingRuns] = useState(true);
  const [loadingLogs, setLoadingLogs] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [rejecting, setRejecting] = useState(false);
  const [promoting, setPromoting] = useState(false);
  const [reviewNotes, setReviewNotes] = useState("");

  const loadContext = useCallback(async () => {
    if (!incident?.id) return;

    try {
      setLoadingContext(true);
      const data = await getRemediationContext(incident.id);
      setContext(data);
    } catch (error) {
      console.log(error);
      toast.error("Failed to load remediation context");
    } finally {
      setLoadingContext(false);
    }
  }, [incident?.id]);

  const loadRuns = useCallback(async () => {
    if (!incident?.id) return;

    try {
      setLoadingRuns(true);
      const data = await getRemediationRunsForIncident(incident.id);
      setRuns(data || []);
      const preferredRun = (data || []).find((run) =>
        ["queued", "approved", "running", "cancel_requested"].includes(
          String(run.status || "").toLowerCase(),
        ),
      );
      setSelectedRunId(preferredRun?.id || data?.[0]?.id || null);
    } catch (error) {
      console.log(error);
      toast.error("Failed to load remediation history");
    } finally {
      setLoadingRuns(false);
    }
  }, [incident?.id]);

  const loadLogs = useCallback(async (remediationRunId) => {
    if (!remediationRunId) {
      setLogs([]);
      return;
    }

    try {
      setLoadingLogs(true);
      const data = await getRemediationRunLogs(remediationRunId);
      setLogs(data || []);
    } catch (error) {
      console.log(error);
      toast.error("Failed to load remediation logs");
    } finally {
      setLoadingLogs(false);
    }
  }, []);

  useEffect(() => {
    setContext(null);
    setRuns([]);
    setLogs([]);
    setSelectedRunId(null);
    setTargetColumn("");
    setReviewNotes("");
    loadContext();
    loadRuns();
  }, [incident?.id, loadContext, loadRuns]);

  useEffect(() => {
    if (!targetColumn && context) {
      setTargetColumn(
        context.suggested_target_column ||
          context.target_candidates?.[0] ||
          "",
      );
    }
  }, [context, targetColumn]);

  useEffect(() => {
    loadLogs(selectedRunId);
  }, [selectedRunId, loadLogs]);

  const activeRun = useMemo(
    () =>
      runs.find((run) =>
        ["queued", "approved", "running", "cancel_requested"].includes(
          String(run.status || "").toLowerCase(),
        ),
      ) || null,
    [runs],
  );

  const reviewRun = useMemo(
    () =>
      runs.find((run) =>
        ["pending_promotion", "completed"].includes(
          String(run.status || "").toLowerCase(),
        ),
      ) || null,
    [runs],
  );

  const latestRun = runs[0] || null;
  const canApprove = Boolean(
    isAdmin &&
      remediation?.allowed_to_execute &&
      remediation?.requires_approval &&
      !activeRun &&
      !reviewRun,
  );
  const canReject = Boolean(
    isAdmin &&
      activeRun &&
      ["queued", "approved", "running"].includes(String(activeRun.status || "").toLowerCase()),
  );
  const canPromote = Boolean(isAdmin && reviewRun);
  const candidateMetrics = remediation?.candidate_metrics || null;

  const handleApprove = async () => {
    const normalizedTarget = targetColumn.trim();
    if (!normalizedTarget) {
      toast.error("Enter the target column before approving retraining.");
      return;
    }

    try {
      setSubmitting(true);
      const response = await approveRemediationForIncident(incident.id, normalizedTarget);
      toast.success(response.message || "Remediation approved.");
      await loadRuns();
      await loadLogs(selectedRunId);
      await onRemediationChanged?.();
    } catch (error) {
      console.log(error);
      toast.error(error?.response?.data?.detail || "Failed to approve remediation.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleReject = async () => {
    if (!activeRun) return;

    try {
      setRejecting(true);
      const response = await rejectRemediationRun(activeRun.id);
      toast.success(response.message || "Remediation rejected.");
      await loadRuns();
      await loadLogs(selectedRunId);
      await onRemediationChanged?.();
    } catch (error) {
      console.log(error);
      toast.error(error?.response?.data?.detail || "Failed to reject remediation.");
    } finally {
      setRejecting(false);
    }
  };

  const handlePromote = async () => {
    if (!reviewRun) return;

    try {
      setPromoting(true);
      const response = await promoteRemediationCandidate(reviewRun.id, reviewNotes.trim());
      toast.success(response.message || "Candidate promoted.");
      await loadRuns();
      await loadLogs(reviewRun.id);
      await onRemediationChanged?.();
    } catch (error) {
      console.log(error);
      toast.error(error?.response?.data?.detail || "Failed to promote the candidate.");
    } finally {
      setPromoting(false);
    }
  };

  const handleRejectCandidate = async () => {
    if (!reviewRun) return;

    try {
      setRejecting(true);
      const response = await rejectRemediationCandidate(reviewRun.id, reviewNotes.trim());
      toast.success(response.message || "Candidate rejected.");
      await loadRuns();
      await loadLogs(reviewRun.id);
      await onRemediationChanged?.();
    } catch (error) {
      console.log(error);
      toast.error(error?.response?.data?.detail || "Failed to reject the candidate.");
    } finally {
      setRejecting(false);
    }
  };

  return (
    <section className="overflow-hidden rounded-xl border border-blue-200 bg-white shadow-[0_4px_24px_rgba(37,99,235,0.08)]">
      <div className="flex flex-col gap-3 border-b border-blue-100 bg-gradient-to-r from-blue-50 to-white px-5 py-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-100 text-blue-700">
              <Wrench size={18} />
            </div>
            <div>
              <p className="text-[14px] font-semibold text-slate-950">Remediation & Approval</p>
              <p className="mt-0.5 text-[12px] text-slate-500">
                Review the recommended action, approve execution, and inspect run logs.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {latestRun && <StatusBadge status={latestRun.status} />}
          <button
            onClick={async () => {
              await loadContext();
              await loadRuns();
            }}
            className="inline-flex items-center gap-2 rounded-md border border-slate-200 bg-white px-3 py-2 text-[12px] font-semibold text-slate-700 transition hover:bg-slate-50"
          >
            <RefreshCw size={14} />
            Refresh
          </button>
        </div>
      </div>

      <div className="grid gap-3 px-5 py-4 md:grid-cols-3">
        <SummaryCard
          label="Action Type"
          value={humanize(remediation?.action_type || "observe")}
          detail={remediation?.recommended_action || "No remediation action has been attached yet."}
          icon={Play}
          tone="blue"
        />
        <SummaryCard
          label="Execution Mode"
          value={humanize(remediation?.action_mode || "none")}
          detail={remediation?.reason || "Execution policy details are not available."}
          icon={ShieldAlert}
          tone="violet"
        />
        <SummaryCard
          label="Latest Run"
          value={latestRun ? humanize(latestRun.status) : "No run started"}
          detail={
            latestRun
              ? latestRun.result_summary || `Triggered ${formatDate(latestRun.created_at)}`
              : "Approval history will appear here after the first remediation run."
          }
          icon={Clock3}
          tone="amber"
        />
      </div>

      {loadingContext ? (
        <div className="border-t border-slate-200 px-5 py-6 text-[13px] text-slate-500">
          Loading remediation context...
        </div>
      ) : (
        <div className="border-t border-slate-200 px-5 py-5">
          <div className="grid gap-4 lg:grid-cols-[minmax(0,1.1fr)_minmax(320px,0.9fr)]">
            <div className="space-y-4">
              <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
                <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">
                  Recommendation
                </p>
                <p className="mt-2 text-[14px] leading-6 text-slate-800">
                  {remediation?.recommended_action ||
                    "This incident does not currently expose a remediation recommendation."}
                </p>
              </div>

              {context?.readiness_warnings?.length > 0 && (
                <div className="rounded-lg border border-amber-200 bg-amber-50 p-4">
                  <div className="flex items-center gap-2 text-amber-800">
                    <AlertCircle size={16} />
                    <p className="text-[12px] font-semibold uppercase tracking-[0.08em]">
                      Readiness Warnings
                    </p>
                  </div>
                  <div className="mt-3 space-y-2 text-[13px] leading-5 text-amber-900">
                    {context.readiness_warnings.map((warning) => (
                      <p key={warning}>{warning}</p>
                    ))}
                  </div>
                </div>
              )}

              <div className="grid gap-3 md:grid-cols-2">
                <div className="rounded-lg border border-slate-200 bg-white p-4">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">
                    Model Context
                  </p>
                  <p className="mt-2 text-[14px] font-semibold text-slate-900">
                    {context?.model_name || "Unknown model"}
                  </p>
                  <p className="mt-1 text-[12px] text-slate-500">
                    Framework: {humanize(context?.model_framework || "unknown")}
                  </p>
                  <p className="mt-1 text-[12px] text-slate-500">
                    Dataset columns: {context?.dataset_columns?.length || 0}
                  </p>
                </div>

                <div className="rounded-lg border border-slate-200 bg-white p-4">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">
                    Feature Setup
                  </p>
                  <p className="mt-2 text-[14px] font-semibold text-slate-900">
                    {context?.expected_features?.length || 0} expected features
                  </p>
                  <p className="mt-1 text-[12px] text-slate-500">
                    {context?.cleaned_data_available
                      ? `Cleaned data is available for retraining. Feature source: ${humanize(
                          context?.expected_features_source || "unknown",
                        )}.`
                      : "Cleaned data is not available for this run."}
                  </p>
                </div>
              </div>
            </div>

            <div className="rounded-lg border border-slate-200 bg-white p-4">
              <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">
                Approval Console
              </p>

              {canApprove ? (
                <div className="mt-3 space-y-4">
                  <div>
                    <label className="block text-[12px] font-medium text-slate-700">
                      Target column
                    </label>
                    <input
                      value={targetColumn}
                      onChange={(event) => setTargetColumn(event.target.value)}
                      list={`target-columns-${incident.id}`}
                      placeholder="Enter target column"
                      className="mt-2 h-11 w-full rounded-md border border-slate-200 bg-slate-50 px-3 text-[14px] text-slate-900 outline-none transition focus:border-blue-300 focus:bg-white"
                    />
                    <datalist id={`target-columns-${incident.id}`}>
                      {(context?.target_candidates || []).map((column) => (
                        <option key={column} value={column} />
                      ))}
                    </datalist>
                    <p className="mt-2 text-[12px] leading-5 text-slate-500">
                      Suggested targets: {(context?.target_candidates || []).slice(0, 6).join(", ") || "None detected yet."}
                    </p>
                  </div>

                  <button
                    onClick={handleApprove}
                    disabled={submitting}
                    className="inline-flex h-11 items-center justify-center gap-2 rounded-md bg-blue-600 px-4 text-[13px] font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    <CheckCircle2 size={15} />
                    {submitting ? "Approving..." : "Approve retraining"}
                  </button>
                </div>
              ) : canReject ? (
                <div className="mt-3 space-y-4">
                  <div className="rounded-lg border border-amber-200 bg-amber-50 p-3">
                    <p className="text-[13px] font-semibold text-amber-900">
                      Remediation run #{activeRun.id} is {humanize(activeRun.status)}.
                    </p>
                    <p className="mt-1 text-[12px] leading-5 text-amber-800">
                      {String(activeRun.status || "").toLowerCase() === "running"
                        ? "You can request cancellation while the run is still executing."
                        : "You can reject the active run before it reaches a terminal state."}
                    </p>
                  </div>
                  <button
                    onClick={handleReject}
                    disabled={rejecting}
                    className="inline-flex h-11 items-center justify-center gap-2 rounded-md border border-red-200 bg-red-50 px-4 text-[13px] font-semibold text-red-700 transition hover:bg-red-100 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    <XCircle size={15} />
                    {rejecting
                      ? "Submitting..."
                      : String(activeRun.status || "").toLowerCase() === "running"
                        ? "Request cancellation"
                        : "Reject remediation"}
                  </button>
                </div>
              ) : canPromote ? (
                <div className="mt-3 space-y-4">
                  <div className="rounded-lg border border-violet-200 bg-violet-50 p-3">
                    <p className="text-[13px] font-semibold text-violet-900">
                      Candidate run #{reviewRun.id} is ready for promotion review.
                    </p>
                    <p className="mt-1 text-[12px] leading-5 text-violet-800">
                      Review the candidate metrics and notes, then promote it to the live alias or reject it.
                    </p>
                  </div>

                  <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                    <p className="text-[12px] font-semibold text-slate-800">
                      Candidate model URI
                    </p>
                    <p className="mt-1 break-all text-[12px] leading-5 text-slate-600">
                      {remediation?.candidate_model_uri || "Candidate artifact URI is not available."}
                    </p>
                    {candidateMetrics && (
                      <div className="mt-3 grid gap-2 md:grid-cols-2">
                        {Object.entries(candidateMetrics).map(([metric, value]) => (
                          <div
                            key={metric}
                            className="rounded-md border border-slate-200 bg-white px-3 py-2"
                          >
                            <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">
                              {humanize(metric)}
                            </p>
                            <p className="mt-1 text-[13px] font-semibold text-slate-900">
                              {typeof value === "number" ? value.toFixed(4) : String(value)}
                            </p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  <div>
                    <label className="block text-[12px] font-medium text-slate-700">
                      Review notes
                    </label>
                    <textarea
                      value={reviewNotes}
                      onChange={(event) => setReviewNotes(event.target.value)}
                      placeholder="Optional review notes for this promotion decision"
                      className="mt-2 min-h-[96px] w-full rounded-md border border-slate-200 bg-slate-50 px-3 py-3 text-[14px] text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-blue-300 focus:bg-white"
                    />
                  </div>

                  <div className="flex flex-col gap-3 sm:flex-row">
                    <button
                      onClick={handlePromote}
                      disabled={promoting}
                      className="inline-flex h-11 items-center justify-center gap-2 rounded-md bg-emerald-600 px-4 text-[13px] font-semibold text-white transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      <CheckCircle2 size={15} />
                      {promoting ? "Promoting..." : "Promote candidate"}
                    </button>
                    <button
                      onClick={handleRejectCandidate}
                      disabled={rejecting}
                      className="inline-flex h-11 items-center justify-center gap-2 rounded-md border border-red-200 bg-red-50 px-4 text-[13px] font-semibold text-red-700 transition hover:bg-red-100 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                      <XCircle size={15} />
                      {rejecting ? "Submitting..." : "Reject candidate"}
                    </button>
                  </div>
                </div>
              ) : (
                <div className="mt-3 rounded-lg border border-slate-200 bg-slate-50 p-4">
                  <p className="text-[13px] font-semibold text-slate-800">
                    {isAdmin
                      ? "No approval action is available right now."
                      : "Only admins can approve or reject remediation."}
                  </p>
                  <p className="mt-1 text-[12px] leading-5 text-slate-500">
                    {remediation?.reason ||
                      "This incident is currently guidance-only or already covered by an existing remediation run."}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      <div className="border-t border-slate-200 px-5 py-5">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <p className="text-[14px] font-semibold text-slate-950">Run History</p>
            <p className="mt-1 text-[12px] text-slate-500">
              Inspect each remediation attempt and its worker log trail.
            </p>
          </div>
        </div>

        {loadingRuns ? (
          <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-5 text-[13px] text-slate-500">
            Loading remediation runs...
          </div>
        ) : runs.length === 0 ? (
          <div className="rounded-lg border border-dashed border-slate-200 bg-slate-50 px-4 py-5 text-[13px] text-slate-500">
            No remediation runs have been created for this incident yet.
          </div>
        ) : (
          <div className="grid gap-4 lg:grid-cols-[minmax(280px,0.9fr)_minmax(0,1.1fr)]">
            <div className="space-y-3">
              {runs.map((run) => (
                <button
                  key={run.id}
                  onClick={() => setSelectedRunId(run.id)}
                  className={`w-full rounded-lg border p-4 text-left transition ${
                    selectedRunId === run.id
                      ? "border-blue-300 bg-blue-50"
                      : "border-slate-200 bg-white hover:bg-slate-50"
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-[13px] font-semibold text-slate-900">
                        Run #{run.id}
                      </p>
                      <p className="mt-1 text-[12px] text-slate-500">
                        {humanize(run.action_type)} via {humanize(run.trigger_mode)}
                      </p>
                    </div>
                    <StatusBadge status={run.status} />
                  </div>
                  <p className="mt-3 text-[12px] leading-5 text-slate-600">
                    {run.result_summary || "No result summary yet."}
                  </p>
                  <p className="mt-2 text-[11px] text-slate-400">
                    Started {formatDate(run.started_at || run.created_at)}
                  </p>
                </button>
              ))}
            </div>

            <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
              <div className="flex items-center justify-between">
                <p className="text-[13px] font-semibold text-slate-900">
                  {selectedRunId ? `Logs for run #${selectedRunId}` : "Action logs"}
                </p>
                {selectedRunId && runs.find((run) => run.id === selectedRunId) && (
                  <StatusBadge status={runs.find((run) => run.id === selectedRunId).status} />
                )}
              </div>

              {loadingLogs ? (
                <div className="mt-4 text-[13px] text-slate-500">Loading logs...</div>
              ) : logs.length === 0 ? (
                <div className="mt-4 text-[13px] text-slate-500">
                  No action logs recorded for this run yet.
                </div>
              ) : (
                <div className="mt-4 space-y-3">
                  {logs.map((log) => (
                    <div
                      key={log.id}
                      className="rounded-md border border-slate-200 bg-white p-3"
                    >
                      <div className="flex flex-col gap-2 lg:flex-row lg:items-center lg:justify-between">
                        <div>
                          <p className="text-[12px] font-semibold text-slate-900">
                            {humanize(log.step_name)}
                          </p>
                          <p className="mt-1 text-[12px] text-slate-500">
                            {log.message}
                          </p>
                        </div>
                        <div className="flex items-center gap-2">
                          <StatusBadge status={log.status} />
                          <span className="text-[11px] text-slate-400">
                            {formatDate(log.created_at)}
                          </span>
                        </div>
                      </div>

                      {log.payload && (
                        <pre className="mt-3 overflow-auto rounded-md bg-slate-950 px-3 py-2 text-[11px] leading-5 text-slate-100">
                          {JSON.stringify(log.payload, null, 2)}
                        </pre>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
