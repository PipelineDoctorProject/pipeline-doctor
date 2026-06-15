import { useCallback, useEffect, useMemo, useRef, useState } from "react";
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
  confirmRemediationDeployment,
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
  staged: "border-blue-200 bg-blue-50 text-blue-700",
  promoted: "border-emerald-200 bg-emerald-100 text-emerald-800",
  deployed: "border-emerald-200 bg-emerald-100 text-emerald-800",
  promotion_rejected: "border-rose-200 bg-rose-50 text-rose-700",
  failed: "border-red-200 bg-red-50 text-red-700",
  blocked: "border-orange-200 bg-orange-50 text-orange-700",
  rejected: "border-slate-200 bg-slate-100 text-slate-700",
  cancel_requested: "border-rose-200 bg-rose-50 text-rose-700",
  canceled: "border-slate-300 bg-slate-100 text-slate-700",
  default: "border-slate-200 bg-slate-50 text-slate-700",
};

const APPROVAL_BLOCKER_STYLES = {
  red: {
    box: "border-red-200 bg-red-50",
    icon: "bg-red-100 text-red-700",
    title: "text-red-950",
    detail: "text-red-800",
    dot: "bg-red-500",
  },
  amber: {
    box: "border-amber-200 bg-amber-50",
    icon: "bg-amber-100 text-amber-700",
    title: "text-amber-950",
    detail: "text-amber-800",
    dot: "bg-amber-500",
  },
  violet: {
    box: "border-violet-200 bg-violet-50",
    icon: "bg-violet-100 text-violet-700",
    title: "text-violet-950",
    detail: "text-violet-800",
    dot: "bg-violet-500",
  },
  blue: {
    box: "border-blue-200 bg-blue-50",
    icon: "bg-blue-100 text-blue-700",
    title: "text-blue-950",
    detail: "text-blue-800",
    dot: "bg-blue-500",
  },
  slate: {
    box: "border-slate-200 bg-slate-50",
    icon: "bg-slate-200 text-slate-700",
    title: "text-slate-900",
    detail: "text-slate-600",
    dot: "bg-slate-400",
  },
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

async function retryOnce(requestFn) {
  try {
    return await requestFn();
  } catch (error) {
    if (error?.code === "ERR_CANCELED") {
      throw error;
    }

    await new Promise((resolve) => setTimeout(resolve, 350));
    return requestFn();
  }
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

function ApprovalBlockerCard({ blocker }) {
  const styles = APPROVAL_BLOCKER_STYLES[blocker?.tone] || APPROVAL_BLOCKER_STYLES.slate;

  return (
    <div className={`mt-3 rounded-lg border p-4 ${styles.box}`}>
      <div className="flex items-start gap-3">
        <div className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${styles.icon}`}>
          <ShieldAlert size={16} />
        </div>
        <div>
          <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">
            Why approval is hidden
          </p>
          <p className={`mt-1 text-[13px] font-semibold ${styles.title}`}>
            {blocker?.title || "No approval action is available right now"}
          </p>
          <p className={`mt-1 text-[12px] leading-5 ${styles.detail}`}>
            {blocker?.detail ||
              "This incident is currently guidance-only or already covered by an existing remediation run."}
          </p>
        </div>
      </div>

      {blocker?.items?.length > 0 && (
        <div className="mt-4 rounded-md border border-white/70 bg-white/60 p-3">
          <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">
            Production next step
          </p>
          <div className="mt-2 space-y-2">
            {blocker.items.map((item) => (
              <div key={item} className="flex gap-2 text-[12px] leading-5 text-slate-700">
                <span className={`mt-2 h-1.5 w-1.5 shrink-0 rounded-full ${styles.dot}`} />
                <span>{item}</span>
              </div>
            ))}
          </div>
        </div>
      )}
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

  const actionType = incident.final_report.action_type;
  const requiresApproval = Boolean(incident.final_report.requires_approval);
  const approvalBackedAction =
    requiresApproval &&
    ["retrain_model", "retrain_clustering", "clustering_retrain"].includes(actionType);
  const manualOnly =
    Boolean(incident.final_report.manual_action_required) && !approvalBackedAction;

  return {
    recommended_action:
      incident.final_report.recommended_action ||
      incident.final_report.action_taken ||
      "Review the final report before executing remediation.",
    action_type: actionType,
    action_mode: incident.final_report.action_mode,
    requires_approval: requiresApproval,
    allowed_to_execute: approvalBackedAction || !manualOnly,
    manual_only: manualOnly,
    reason:
      incident.final_report.timeline_summary ||
      incident.final_report.action_taken ||
      "Refer to the final incident report for lifecycle details.",
  };
}

const SOURCE_DATA_FAILURE_TYPES = new Set([
  "SCHEMA_MISMATCH",
  "MISSING_COLUMNS",
  "EXTRA_COLUMNS",
  "DATA_QUALITY",
  "NULL_SPIKE",
  "RANGE_VIOLATION",
  "CATEGORICAL_SHIFT",
]);

const RETRAINING_FAILURE_TYPES = new Set([
  "DATA_DRIFT",
  "CONCEPT_DRIFT",
  "MODEL_DEGRADATION",
]);

function extractFailureTypes(incident) {
  const sources = [
    incident?.remediation?.failure_types,
    incident?.final_report?.failure_types,
    incident?.report?.failure_types,
    incident?.rca_report?.failure_types,
  ];

  return [
    ...new Set(
      sources
        .flatMap((value) => (Array.isArray(value) ? value : []))
        .map((value) => String(value || "").trim().toUpperCase())
        .filter(Boolean),
    ),
  ];
}

function getIncidentSeverity(incident, remediation) {
  return String(
    remediation?.severity ||
      incident?.severity ||
      incident?.final_report?.severity ||
      incident?.report?.severity ||
      "",
  ).toLowerCase();
}

function buildApprovalBlocker({
  incident,
  remediation,
  context,
  activeRun,
  reviewRun,
  stagedRun,
  terminalRun,
  isAdmin,
}) {
  const failureTypes = extractFailureTypes(incident);
  const sourceDataBlockers = failureTypes.filter((type) => SOURCE_DATA_FAILURE_TYPES.has(type));
  const hasRetrainingSignal = failureTypes.some((type) => RETRAINING_FAILURE_TYPES.has(type));
  const severity = getIncidentSeverity(incident, remediation);

  if (!isAdmin) {
    return {
      tone: "slate",
      title: "Admin approval required",
      detail: "Only workspace admins can approve retraining, stage candidates, reject runs, or confirm deployment.",
      items: ["Ask a workspace admin to review this incident and choose the next production action."],
    };
  }

  if (activeRun) {
    return {
      tone: "amber",
      title: `Remediation run #${activeRun.id} is already ${humanize(activeRun.status)}`,
      detail: "OpsSight allows one active remediation run per incident to avoid duplicate candidate models and conflicting state transitions.",
      items: ["Wait for the run to finish, or request cancellation if the current run is no longer valid."],
    };
  }

  if (reviewRun) {
    return {
      tone: "violet",
      title: `Candidate run #${reviewRun.id} is waiting for promotion review`,
      detail: "A candidate model already exists. Review its metrics and either stage or reject it before starting another retraining run.",
      items: ["Use Stage candidate to move it to the staging alias, or Reject candidate to discard it."],
    };
  }

  if (stagedRun) {
    return {
      tone: "blue",
      title: `Candidate run #${stagedRun.id} is already staged`,
      detail: "The model is waiting for deployment confirmation. OpsSight should not create another candidate until CI/CD finishes deploying this staged version.",
      items: ["Deploy the staged MLflow alias in your serving pipeline, run smoke tests, then confirm deployment here."],
    };
  }

  if (terminalRun) {
    return {
      tone: "blue",
      title: `Remediation run #${terminalRun.id} is already ${humanize(terminalRun.status)}`,
      detail:
        "The candidate lifecycle for this incident is complete, so OpsSight should not start another retraining run for the same incident.",
      items: [
        "Monitor the promoted model version in the next production DAG runs.",
        "Resolve or close this incident after confirming production health checks, Slack alerts, and report records are correct.",
      ],
    };
  }

  if (severity === "critical") {
    return {
      tone: "red",
      title: "Critical incident is manual-first",
      detail: "For production safety, critical incidents are not retrained directly from the failed batch. The source issue must be validated or fixed first.",
      items: [
        sourceDataBlockers.length
          ? `Blocking evidence: ${sourceDataBlockers.map(humanize).join(", ")}.`
          : "Review the RCA report and validate the production data source.",
        "Fix the upstream data, schema, or ingestion problem, then rerun the DAG with corrected data.",
        "Approve retraining only if the next incident is a retraining-safe drift or model degradation case.",
      ],
    };
  }

  if (sourceDataBlockers.length > 0) {
    return {
      tone: "amber",
      title: "Retraining is blocked by data or schema quality",
      detail: "The approval button appears only after the batch is safe enough to train from. This incident still contains source-data problems.",
      items: [
        `Blocking evidence: ${sourceDataBlockers.map(humanize).join(", ")}.`,
        "Fix or approve the source/schema change, rerun the DAG, and use the new incident for remediation approval.",
      ],
    };
  }

  if (context?.cleaned_data_available === false) {
    return {
      tone: "amber",
      title: "Cleaned training data is not available",
      detail: "Retraining needs a validated cleaned dataset from the pipeline run before OpsSight can create a candidate model.",
      items: ["Rerun the DAG and confirm the cleaned output is saved before approving remediation."],
    };
  }

  if (remediation?.manual_only) {
    return {
      tone: "slate",
      title: "Manual investigation required",
      detail:
        remediation?.reason ||
        "The current remediation policy marked this incident as guidance-only.",
      items: ["Document the investigation outcome, fix the source issue, and rerun monitoring."],
    };
  }

  if (remediation?.requires_approval && !hasRetrainingSignal) {
    return {
      tone: "slate",
      title: "No retraining-safe signal was detected",
      detail: "Production retraining approval is shown only for drift, concept drift, or model degradation without data/schema blockers.",
      items: ["Use the RCA report to decide whether this is a source fix, schema approval, or baseline refresh instead."],
    };
  }

  if (remediation && !remediation.allowed_to_execute) {
    return {
      tone: "slate",
      title: "Remediation execution is disabled by policy",
      detail:
        remediation?.reason ||
        "The backend remediation policy did not allow this incident to start a retraining run.",
      items: ["Review the report recommendation and rerun the pipeline after the production issue is resolved."],
    };
  }

  return {
    tone: "slate",
    title: "No approval action is available right now",
    detail:
      remediation?.reason ||
      "This incident is currently guidance-only, already resolved, or not eligible for automated remediation.",
    items: ["Review the report and keep the incident open until the owner documents the next action."],
  };
}

export default function IncidentRemediationPanel({
  incident,
  onRemediationChanged,
}) {
  const user = useAuthStore((state) => state.user);
  const isAdmin = user?.role === "admin";
  const remediation = deriveRemediationSummary(incident);
  const incidentId = incident?.id;

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
  const [confirmingDeployment, setConfirmingDeployment] = useState(false);
  const [reviewNotes, setReviewNotes] = useState("");
  const loadVersionRef = useRef(0);

  const loadContext = useCallback(async (version = loadVersionRef.current) => {
    if (!incidentId) return;

    try {
      setLoadingContext(true);
      const data = await retryOnce(() => getRemediationContext(incidentId));
      if (version !== loadVersionRef.current) return;
      setContext(data);
    } catch (error) {
      console.log(error);
      if (version === loadVersionRef.current) {
        toast.error("Failed to load remediation context", {
          id: `remediation-context-${incidentId}`,
        });
      }
    } finally {
      if (version === loadVersionRef.current) {
        setLoadingContext(false);
      }
    }
  }, [incidentId]);

  const loadRuns = useCallback(async (version = loadVersionRef.current) => {
    if (!incidentId) return;

    try {
      setLoadingRuns(true);
      const data = await retryOnce(() => getRemediationRunsForIncident(incidentId));
      if (version !== loadVersionRef.current) return;
      setRuns(data || []);
      const preferredRun = (data || []).find((run) =>
        ["queued", "approved", "running", "cancel_requested"].includes(
          String(run.status || "").toLowerCase(),
        ),
      );
      setSelectedRunId(preferredRun?.id || data?.[0]?.id || null);
    } catch (error) {
      console.log(error);
      if (version === loadVersionRef.current) {
        toast.error("Failed to load remediation history", {
          id: `remediation-runs-${incidentId}`,
        });
      }
    } finally {
      if (version === loadVersionRef.current) {
        setLoadingRuns(false);
      }
    }
  }, [incidentId]);

  const loadLogs = useCallback(async (remediationRunId, version = loadVersionRef.current) => {
    if (!remediationRunId) {
      setLogs([]);
      return;
    }

    try {
      setLoadingLogs(true);
      const data = await retryOnce(() => getRemediationRunLogs(remediationRunId));
      if (version !== loadVersionRef.current) return;
      setLogs(data || []);
    } catch (error) {
      console.log(error);
      if (version === loadVersionRef.current) {
        toast.error("Failed to load remediation logs", {
          id: `remediation-logs-${remediationRunId}`,
        });
      }
    } finally {
      if (version === loadVersionRef.current) {
        setLoadingLogs(false);
      }
    }
  }, []);

  useEffect(() => {
    const version = loadVersionRef.current + 1;
    loadVersionRef.current = version;
    setContext(null);
    setRuns([]);
    setLogs([]);
    setSelectedRunId(null);
    setTargetColumn("");
    setReviewNotes("");
    loadContext(version);
    loadRuns(version);
  }, [incidentId, loadContext, loadRuns]);

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
    loadLogs(selectedRunId, loadVersionRef.current);
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

  const stagedRun = useMemo(
    () =>
      runs.find((run) => String(run.status || "").toLowerCase() === "staged") || null,
    [runs],
  );

  const terminalRun = useMemo(
    () =>
      runs.find((run) =>
        ["deployed", "promoted"].includes(String(run.status || "").toLowerCase()),
      ) || null,
    [runs],
  );

  const latestRun = runs[0] || null;
  const canApprove = Boolean(
    isAdmin &&
      remediation?.allowed_to_execute &&
      remediation?.requires_approval &&
      !activeRun &&
      !reviewRun &&
      !stagedRun &&
      !terminalRun,
  );
  const canReject = Boolean(
    isAdmin &&
      activeRun &&
      ["queued", "approved", "running"].includes(String(activeRun.status || "").toLowerCase()),
  );
  const canPromote = Boolean(isAdmin && reviewRun);
  const canConfirmDeployment = Boolean(isAdmin && stagedRun);
  const approvalBlocker = buildApprovalBlocker({
    incident,
    remediation,
    context,
    activeRun,
    reviewRun,
    stagedRun,
    terminalRun,
    isAdmin,
  });
  const candidateLogPayload = useMemo(() => {
    const matchingPayload = logs
      .map((log) => log?.payload)
      .find((payload) => payload?.candidate_model_uri || payload?.candidate_mlflow_run_id);
    return matchingPayload || null;
  }, [logs]);
  const candidateMetrics =
    remediation?.candidate_metrics || candidateLogPayload?.metrics || null;
  const candidateModelUri =
    remediation?.candidate_model_uri || candidateLogPayload?.candidate_model_uri || "";
  const stagedModelUri =
    remediation?.staged_model_uri ||
    remediation?.promoted_model_uri ||
    candidateLogPayload?.staged_model_uri ||
    candidateLogPayload?.promoted_model_uri ||
    "";
  const targetRequired = context?.target_required !== false;
  const trainingMode = context?.training_mode || "supervised";

  const handleApprove = async () => {
    const normalizedTarget = targetColumn.trim();
    if (targetRequired && !normalizedTarget) {
      toast.error("Enter the target column before approving retraining.");
      return;
    }

    try {
      setSubmitting(true);
      const response = await approveRemediationForIncident(
        incidentId,
        targetRequired ? normalizedTarget : null,
      );
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
      toast.success(response.message || "Candidate staged.");
      await loadRuns();
      await loadLogs(reviewRun.id);
      await onRemediationChanged?.();
    } catch (error) {
      console.log(error);
      toast.error(error?.response?.data?.detail || "Failed to stage the candidate.");
    } finally {
      setPromoting(false);
    }
  };

  const handleConfirmDeployment = async () => {
    if (!stagedRun) return;

    try {
      setConfirmingDeployment(true);
      const response = await confirmRemediationDeployment(stagedRun.id, reviewNotes.trim());
      toast.success(response.message || "Deployment confirmed.");
      await loadRuns();
      await loadLogs(stagedRun.id);
      await onRemediationChanged?.();
    } catch (error) {
      console.log(error);
      toast.error(error?.response?.data?.detail || "Failed to confirm deployment.");
    } finally {
      setConfirmingDeployment(false);
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
                    Training mode: {humanize(trainingMode)}
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
                  {targetRequired ? (
                    <div>
                      <label className="block text-[12px] font-medium text-slate-700">
                        Target column
                      </label>
                      <input
                        value={targetColumn}
                        onChange={(event) => setTargetColumn(event.target.value)}
                        list={`target-columns-${incidentId}`}
                        placeholder="Enter target column"
                        className="mt-2 h-11 w-full rounded-md border border-slate-200 bg-slate-50 px-3 text-[14px] text-slate-900 outline-none transition focus:border-blue-300 focus:bg-white"
                      />
                      <datalist id={`target-columns-${incidentId}`}>
                        {(context?.target_candidates || []).map((column) => (
                          <option key={column} value={column} />
                        ))}
                      </datalist>
                      <p className="mt-2 text-[12px] leading-5 text-slate-500">
                        Suggested targets: {(context?.target_candidates || []).slice(0, 6).join(", ") || "None detected yet."}
                      </p>
                    </div>
                  ) : (
                    <div className="rounded-lg border border-blue-100 bg-blue-50 p-3">
                      <p className="text-[13px] font-semibold text-blue-900">
                        Feature-only clustering retrain
                      </p>
                      <p className="mt-1 text-[12px] leading-5 text-blue-800">
                        This model is treated as unsupervised, so remediation will refit the clustering estimator using the resolved feature columns. No target column is required.
                      </p>
                    </div>
                  )}

                  <button
                    onClick={handleApprove}
                    disabled={submitting}
                    className="inline-flex h-11 items-center justify-center gap-2 rounded-md bg-blue-600 px-4 text-[13px] font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    <CheckCircle2 size={15} />
                    {submitting
                      ? "Approving..."
                      : targetRequired
                        ? "Approve retraining"
                        : "Approve clustering retrain"}
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
                      Candidate run #{reviewRun.id} is ready for staging review.
                    </p>
                    <p className="mt-1 text-[12px] leading-5 text-violet-800">
                      Review the candidate metrics and notes, then stage it for deployment or reject it. The live champion alias will not change yet.
                    </p>
                  </div>

                  <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
                    <p className="text-[12px] font-semibold text-slate-800">
                      Candidate model URI
                    </p>
                    <p className="mt-1 break-all text-[12px] leading-5 text-slate-600">
                      {candidateModelUri || "Candidate artifact URI is not available."}
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
                      placeholder="Optional review notes for this staging decision"
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
                      {promoting ? "Staging..." : "Stage candidate"}
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
              ) : canConfirmDeployment ? (
                <div className="mt-3 space-y-4">
                  <div className="rounded-lg border border-blue-200 bg-blue-50 p-3">
                    <p className="text-[13px] font-semibold text-blue-900">
                      Candidate run #{stagedRun.id} is staged for deployment.
                    </p>
                    <p className="mt-1 text-[12px] leading-5 text-blue-800">
                      Your deployment pipeline should now deploy the MLflow staging alias. Confirm deployment only after smoke tests and serving health checks pass.
                    </p>
                    {stagedModelUri && (
                      <p className="mt-2 break-all rounded-md bg-white/70 px-3 py-2 text-[12px] leading-5 text-blue-900">
                        Staged model URI: {stagedModelUri}
                      </p>
                    )}
                  </div>

                  <div>
                    <label className="block text-[12px] font-medium text-slate-700">
                      Deployment notes
                    </label>
                    <textarea
                      value={reviewNotes}
                      onChange={(event) => setReviewNotes(event.target.value)}
                      placeholder="Optional deployment confirmation notes"
                      className="mt-2 min-h-[96px] w-full rounded-md border border-slate-200 bg-slate-50 px-3 py-3 text-[14px] text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-blue-300 focus:bg-white"
                    />
                  </div>

                  <button
                    onClick={handleConfirmDeployment}
                    disabled={confirmingDeployment}
                    className="inline-flex h-11 items-center justify-center gap-2 rounded-md bg-emerald-600 px-4 text-[13px] font-semibold text-white transition hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    <CheckCircle2 size={15} />
                    {confirmingDeployment ? "Confirming..." : "Confirm deployment"}
                  </button>
                </div>
              ) : (
                <ApprovalBlockerCard blocker={approvalBlocker} />
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
