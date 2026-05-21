import { useEffect, useMemo, useState, useCallback, useRef } from "react";
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  Clock3,
  Eye,
  ExternalLink,
  Info,
  RefreshCw,
  Search,
  ShieldAlert,
  X,
} from "lucide-react";
import toast from "react-hot-toast";
import { getIncidents } from "../../store/incidentStore";
import { getIncidentAgentRuns, getAgentRunSteps } from "../../store/agentStore";
import { useSearchParams } from "react-router-dom";
import useSelectedModelStore from "../../store/selectedModelStore";
import useAgentWebSocket from "../../hooks/useAgentWebSocket";
import useIncidentsWebSocket from "../../hooks/useIncidentsWebSocket";
import AgentTraceStepper from "../../components/agents/AgentTraceStepper";
import IncidentReasoningCard from "../../components/agents/IncidentReasoningCard";

const severityConfig = {
  critical: {
    className: "border-red-200 bg-red-50 text-red-700",
    icon: ShieldAlert,
  },
  high: {
    className: "border-orange-200 bg-orange-50 text-orange-700",
    icon: AlertTriangle,
  },
  medium: {
    className: "border-amber-200 bg-amber-50 text-amber-700",
    icon: AlertCircle,
  },
  low: {
    className: "border-blue-200 bg-blue-50 text-blue-700",
    icon: Info,
  },
  default: {
    className: "border-slate-200 bg-slate-50 text-slate-700",
    icon: Info,
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

function getSeverityMeta(severity) {
  return severityConfig[String(severity || "").toLowerCase()] || severityConfig.default;
}

function isResolved(status) {
  const normalized = String(status || "").toLowerCase();
  return normalized === "resolved" || normalized === "closed";
}

function getSeverityRank(severity) {
  const ranks = { critical: 4, high: 3, medium: 2, low: 1 };
  return ranks[String(severity || "").toLowerCase()] || 0;
}

function getWorstSeverity(incidents) {
  return incidents.reduce((worst, incident) => {
    return getSeverityRank(incident.severity) > getSeverityRank(worst)
      ? incident.severity
      : worst;
  }, "low");
}

function groupIncidentsByRun(incidents) {
  return Array.from(
    incidents
      .reduce((groups, incident) => {
        const runId = incident.run_id || "unknown";
        const group = groups.get(runId) || {
          runId,
          incidents: [],
          open: 0,
          resolved: 0,
          severity: "low",
          latestAt: null,
        };

        group.incidents.push(incident);
        if (isResolved(incident.status)) group.resolved += 1;
        else group.open += 1;
        group.severity = getWorstSeverity(group.incidents);

        if (incident.created_at) {
          const currentTime = new Date(incident.created_at).getTime();
          const latestTime = group.latestAt ? new Date(group.latestAt).getTime() : 0;
          if (Number.isFinite(currentTime) && currentTime > latestTime) {
            group.latestAt = incident.created_at;
          }
        }

        groups.set(runId, group);
        return groups;
      }, new Map())
      .values(),
  ).sort((a, b) => Number(b.runId) - Number(a.runId));
}

function humanizeType(value) {
  return String(value || "unknown")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function getIncidentGuidance(incident) {
  if (incident.guidance?.cause || incident.guidance?.action) {
    return {
      cause: incident.guidance.cause || "No cause was returned for this incident.",
      action: incident.guidance.action || "Review the related pipeline evidence.",
      source: incident.guidance.source,
      model: incident.guidance.model,
    };
  }

  const type = String(incident.failure_type || "").toLowerCase();

  if (type.includes("drift")) {
    return {
      cause: "The current batch distribution moved away from the baseline population.",
      action: "Compare drift details with the source time window, campaign, region, or upstream feed before retraining or refreshing the baseline.",
    };
  }

  if (type.includes("schema")) {
    return {
      cause: "The incoming contract changed, usually because columns were added, removed, renamed, or typed differently.",
      action: "Approve schema changes only when expected; otherwise restore the upstream contract before using this run for decisions.",
    };
  }

  if (type.includes("quality")) {
    return {
      cause: "Validation checks found missing values, invalid values, unseen categories, or out-of-range records.",
      action: "Open Data Quality for row-level evidence, fix bad values upstream, then rerun validation.",
    };
  }

  return {
    cause: "The RCA pipeline escalated this run because one or more monitoring signals crossed severity thresholds.",
    action: "Review Data Quality and Drift details together to decide whether this is bad data, expected change, or stale monitoring baseline.",
  };
}

function buildIncidentRunSummary(run) {
  if (!run) return [];

  const types = Array.from(
    new Set(run.incidents.map((incident) => humanizeType(incident.failure_type))),
  );
  const rcaIncident = run.incidents.find((incident) => incident.rca_report);
  const rcaReport = rcaIncident?.rca_report;

  return [
    {
      label: "RCA status",
      value:
        run.open > 0
          ? `${run.open} open incident${run.open === 1 ? "" : "s"}`
          : "All incidents resolved",
      detail: rcaReport
        ? `Reasoning source: ${rcaReport.provider || "fallback"} / ${rcaReport.model || "deterministic-rules"}.`
        : run.open > 0
          ? "Triage the highest severity item first."
          : "No open action remains for this run.",
    },
    {
      label: "Failure groups",
      value: types.slice(0, 3).join(", ") || "Unknown",
      detail:
        types.length > 3
          ? `+${types.length - 3} additional type${types.length - 3 === 1 ? "" : "s"}.`
          : "Types are grouped from stored incident records.",
    },
    {
      label: "Recommended path",
      value: rcaReport?.recommendation ? "RCA recommendation" : "Use evidence pages together",
      detail:
        rcaReport?.recommendation ||
        "Open Data Quality for validation causes, Drift for distribution shift, and Pipelines for cleaned data.",
    },
  ];
}

function buildIncidentSnapshotMap(incidents = []) {
  return incidents.reduce((snapshot, incident) => {
    snapshot.set(String(incident.id), {
      runId: incident.run_id,
      severity: incident.severity,
      status: incident.status,
    });
    return snapshot;
  }, new Map());
}

function getReportingStepStatus(steps = []) {
  if (!Array.isArray(steps) || steps.length === 0) return null;

  const reportingByIndex = steps.find((step) => Number(step?.step_index) === 3);
  if (reportingByIndex?.status) {
    return String(reportingByIndex.status).toLowerCase();
  }

  const reportingByName = steps.find(
    (step) => String(step?.step_name || "").toLowerCase() === "reporting",
  );
  if (reportingByName?.status) {
    return String(reportingByName.status).toLowerCase();
  }

  // Stored log rows often omit status and only indicate that the step exists.
  if (reportingByIndex || reportingByName) {
    return "done";
  }

  return null;
}

function isRcaReportReady({
  latestAgentRunStatus,
  shouldShowLiveTrace,
  liveSteps,
  storedSteps,
  liveRunStatus,
}) {
  const normalizedLatestStatus = String(latestAgentRunStatus || "").toLowerCase();
  const normalizedLiveRunStatus = String(liveRunStatus || "").toLowerCase();

  if (shouldShowLiveTrace) {
    const liveReportingStatus = getReportingStepStatus(liveSteps);
    if (liveReportingStatus === "done") return true;
    if (normalizedLiveRunStatus === "complete") return true;
    return false;
  }

  const storedReportingStatus = getReportingStepStatus(storedSteps);
  if (storedReportingStatus === "done") return true;

  return normalizedLatestStatus === "completed" || normalizedLatestStatus === "complete";
}

function formatRunSummary(runIds = []) {
  const uniqueRunIds = Array.from(
    new Set(runIds.map((runId) => String(runId || "")).filter(Boolean)),
  );

  if (uniqueRunIds.length === 0) return "";

  const preview = uniqueRunIds.slice(0, 3).map((runId) => `#${runId}`).join(", ");
  return uniqueRunIds.length > 3
    ? `${preview} +${uniqueRunIds.length - 3} more`
    : preview;
}

function summarizeIncidentDelta(previousSnapshot, nextIncidents = []) {
  const nextSnapshot = buildIncidentSnapshotMap(nextIncidents);
  let newOpenCount = 0;
  let newCriticalCount = 0;
  let resolvedCount = 0;
  const newRunIds = [];
  const resolvedRunIds = [];

  nextIncidents.forEach((incident) => {
    const previousIncident = previousSnapshot.get(String(incident.id));
    const nowResolved = isResolved(incident.status);
    const wasResolved = previousIncident ? isResolved(previousIncident.status) : null;
    const isCritical = String(incident.severity || "").toLowerCase() === "critical";

    if ((!previousIncident || wasResolved) && !nowResolved) {
      newOpenCount += 1;
      newRunIds.push(incident.run_id);
      if (isCritical) newCriticalCount += 1;
    }

    if (previousIncident && !wasResolved && nowResolved) {
      resolvedCount += 1;
      resolvedRunIds.push(incident.run_id);
    }
  });

  return {
    nextSnapshot,
    newOpenCount,
    newCriticalCount,
    resolvedCount,
    newRunIds,
    resolvedRunIds,
  };
}

export default function IncidentsPage() {
  const connectedTraceRunIdRef = useRef(null);
  const incidentSnapshotRef = useRef(new Map());
  const hasBootstrappedIncidentsRef = useRef(false);
  const processedLiveEventRef = useRef(new Set());
  const [searchParams] = useSearchParams();
  const runParam = searchParams.get("run");
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [selectedRunId, setSelectedRunId] = useState(runParam);
  const selectedModelId = useSelectedModelStore((state) => state.selectedModelId);

  const [agentRuns, setAgentRuns] = useState([]);
  const [agentSteps, setAgentSteps] = useState([]);
  const [agentLoading, setAgentLoading] = useState(false);

  const {
    steps: wsSteps,
    isLive,
    runStatus,
    lastMessage,
    connect: wsConnect,
    disconnect: wsDisconnect,
  } = useAgentWebSocket();
  const {
    lastMessage: lastIncidentMessage,
    connect: connectIncidentsFeed,
    disconnect: disconnectIncidentsFeed,
  } = useIncidentsWebSocket();

  const loadIncidents = useCallback(
    async ({ silent = false, announceDelta = false } = {}) => {
      try {
        if (!silent) {
          setLoading(true);
        }

        const data = await getIncidents(selectedModelId);
        const nextIncidents = data || [];
        const previousSnapshot = incidentSnapshotRef.current;

        if (announceDelta && hasBootstrappedIncidentsRef.current) {
          const delta = summarizeIncidentDelta(previousSnapshot, nextIncidents);
          const newRunSummary = formatRunSummary(delta.newRunIds);
          const resolvedRunSummary = formatRunSummary(delta.resolvedRunIds);

          if (delta.newCriticalCount > 0) {
            toast.error(
              `${delta.newCriticalCount} new critical incident${delta.newCriticalCount === 1 ? "" : "s"} detected${newRunSummary ? ` in runs ${newRunSummary}` : ""}`,
            );
          } else if (delta.newOpenCount > 0) {
            toast(
              `${delta.newOpenCount} new incident${delta.newOpenCount === 1 ? "" : "s"} detected${newRunSummary ? ` in runs ${newRunSummary}` : ""}`,
            );
          }

          if (delta.resolvedCount > 0) {
            toast.success(
              `${delta.resolvedCount} incident${delta.resolvedCount === 1 ? "" : "s"} resolved${resolvedRunSummary ? ` in runs ${resolvedRunSummary}` : ""}`,
            );
          }

          incidentSnapshotRef.current = delta.nextSnapshot;
        } else {
          incidentSnapshotRef.current = buildIncidentSnapshotMap(nextIncidents);
        }

        hasBootstrappedIncidentsRef.current = true;
        setIncidents(nextIncidents);
      } catch (err) {
        console.log(err);
        toast.error("Failed to load incidents");
      } finally {
        if (!silent) {
          setLoading(false);
        }
      }
    },
    [selectedModelId],
  );

  const loadAgentData = useCallback(
    async (incidentId, { silent = false } = {}) => {
      if (!incidentId) return;
      try {
        if (!silent) {
          setAgentLoading(true);
          setAgentRuns([]);
          setAgentSteps([]);
        }

        const runs = await getIncidentAgentRuns(incidentId);
        setAgentRuns(runs || []);

        if (!runs || runs.length === 0) {
          setAgentSteps([]);
          if (connectedTraceRunIdRef.current !== null) {
            wsDisconnect();
            connectedTraceRunIdRef.current = null;
          }
          return;
        }

        const latestRun = runs[0];
        const steps = await getAgentRunSteps(latestRun.id);
        setAgentSteps(steps || []);

        if (latestRun.status === "running") {
          if (connectedTraceRunIdRef.current !== latestRun.pipeline_run_id) {
            wsConnect(latestRun.pipeline_run_id);
            connectedTraceRunIdRef.current = latestRun.pipeline_run_id;
          }
        } else if (connectedTraceRunIdRef.current !== null) {
          wsDisconnect();
          connectedTraceRunIdRef.current = null;
        }
      } catch (err) {
        console.log("Agent data load error:", err);
      } finally {
        if (!silent) {
          setAgentLoading(false);
        }
      }
    },
    [wsConnect, wsDisconnect],
  );

  useEffect(() => {
    loadIncidents({ announceDelta: false });
  }, [loadIncidents]);

  useEffect(() => {
    connectIncidentsFeed();

    return () => {
      disconnectIncidentsFeed();
    };
  }, [connectIncidentsFeed, disconnectIncidentsFeed]);

  useEffect(() => {
    if (!lastIncidentMessage) return;
    if (!["incident_created", "incident_updated"].includes(lastIncidentMessage.event)) return;

    loadIncidents({ silent: true, announceDelta: true });
  }, [lastIncidentMessage, loadIncidents]);

  useEffect(() => {
    processedLiveEventRef.current.clear();
  }, [selectedRunId]);

  const filteredIncidents = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return incidents;

    return incidents.filter((incident) =>
      [
        incident.title,
        incident.description,
        incident.failure_type,
        incident.severity,
        incident.status,
        incident.run_id,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(needle),
    );
  }, [incidents, query]);

  const openCount = incidents.filter((incident) => !isResolved(incident.status)).length;
  const criticalCount = incidents.filter(
    (incident) => String(incident.severity || "").toLowerCase() === "critical",
  ).length;
  const resolvedCount = incidents.filter((incident) => isResolved(incident.status)).length;
  const groupedRuns = useMemo(
    () => groupIncidentsByRun(filteredIncidents),
    [filteredIncidents],
  );
  const selectedRun = groupedRuns.find(
    (group) => String(group.runId) === String(selectedRunId),
  );
  const selectedRcaIncident = selectedRun?.incidents.find((incident) => incident.rca_report);
  const selectedRcaReport = selectedRcaIncident?.rca_report ?? null;
  const displayAgentSteps = agentSteps;
  const latestAgentRunStatus = agentRuns[0]?.status;
  const selectedRunIdLabel = String(selectedRun?.runId ?? "");
  const liveTraceRunId = String(
    lastMessage?.run_id ?? connectedTraceRunIdRef.current ?? "",
  );
  const hasLiveTraceSteps = wsSteps.some(
    (step) => step.status !== "pending" || Boolean(step.message),
  );
  const shouldShowLiveTrace =
    hasLiveTraceSteps &&
    liveTraceRunId === selectedRunIdLabel &&
    ["running", "complete", "failed"].includes(runStatus);
  const shouldShowRcaReport =
    Boolean(selectedRcaReport) &&
    isRcaReportReady({
      latestAgentRunStatus,
      shouldShowLiveTrace,
      liveSteps: wsSteps,
      storedSteps: displayAgentSteps,
      liveRunStatus: runStatus,
    });

  useEffect(() => {
    if (!selectedRun || !lastMessage) return;
    if (!["run_complete", "run_failed"].includes(lastMessage.event)) return;
    if (String(lastMessage.run_id) !== String(selectedRun.runId)) return;

    const eventKey = `${lastMessage.event}:${lastMessage.run_id}:${lastMessage.message || ""}`;
    if (processedLiveEventRef.current.has(eventKey)) return;
    processedLiveEventRef.current.add(eventKey);

    const firstIncident = selectedRun.incidents?.[0];

    if (lastMessage.event === "run_complete") {
      toast.success("AI Agent run completed. RCA is ready.");
    } else {
      toast.error("AI Agent run failed. Check the stored trace for the last completed step.");
    }

    loadIncidents({ silent: true, announceDelta: true });

    if (firstIncident?.id) {
      loadAgentData(firstIncident.id, { silent: true });
    }
  }, [lastMessage, selectedRun, loadAgentData, loadIncidents]);

  useEffect(() => {
    if (!selectedRun) {
      setAgentRuns([]);
      setAgentSteps([]);
      connectedTraceRunIdRef.current = null;
      wsDisconnect();
      return;
    }

    const firstIncident = selectedRun.incidents?.[0];
    if (firstIncident?.id) {
      loadAgentData(firstIncident.id);
    }
  }, [selectedRun, loadAgentData, wsDisconnect]);

  useEffect(() => {
    if (!selectedRun) return undefined;

    const firstIncident = selectedRun.incidents?.[0];
    if (!firstIncident?.id) return undefined;

    const shouldPoll = agentRuns.length === 0 || latestAgentRunStatus === "running";

    if (!shouldPoll) return undefined;

    const intervalId = window.setInterval(() => {
      loadAgentData(firstIncident.id, { silent: true });
    }, 2000);

    return () => window.clearInterval(intervalId);
  }, [selectedRun, agentRuns.length, latestAgentRunStatus, loadAgentData]);

  return (
    <div className="flex flex-col gap-5">
      <section className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-[0_12px_34px_rgba(15,23,42,0.04)]">
        <div className="flex flex-col gap-5 border-b border-slate-200 px-6 py-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-[760px]">
            <h1 className="text-[30px] font-semibold leading-tight text-slate-950">
              Incidents
            </h1>

            <p className="mt-2 text-[14px] leading-6 text-slate-500">
              Triage alerts created from severe drift, schema changes, and data
              quality failures across production model runs.
            </p>
          </div>

          <button
            onClick={() => loadIncidents({ announceDelta: false })}
            className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-slate-950 px-4 text-[13px] font-semibold text-white transition hover:bg-slate-800"
          >
            <RefreshCw size={15} />
            Refresh Incidents
          </button>
        </div>

        <div className="grid border-b border-slate-200 md:grid-cols-3">
          <div className="border-b border-slate-200 px-6 py-4 md:border-b-0 md:border-r">
            <div className="flex items-center justify-between text-[12px] font-medium text-slate-500">
              Open incidents
              <AlertTriangle size={16} />
            </div>
            <div className="mt-2 text-[26px] font-semibold text-slate-950">
              {openCount}
            </div>
          </div>

          <div className="border-b border-slate-200 px-6 py-4 md:border-b-0 md:border-r">
            <div className="flex items-center justify-between text-[12px] font-medium text-slate-500">
              Critical severity
              <ShieldAlert size={16} />
            </div>
            <div className="mt-2 text-[26px] font-semibold text-slate-950">
              {criticalCount}
            </div>
          </div>

          <div className="px-6 py-4">
            <div className="flex items-center justify-between text-[12px] font-medium text-slate-500">
              Resolved
              <CheckCircle2 size={16} />
            </div>
            <div className="mt-2 text-[26px] font-semibold text-slate-950">
              {resolvedCount}
            </div>
          </div>
        </div>
      </section>

      <section className="rounded-lg border border-slate-200 bg-white shadow-[0_12px_34px_rgba(15,23,42,0.04)]">
        <div className="flex flex-col gap-4 border-b border-slate-200 px-5 py-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-[16px] font-semibold text-slate-950">
              Incident Runs
            </h2>
            <p className="mt-1 text-[13px] text-slate-500">
              Use View details to inspect each incident raised inside a run.
            </p>
          </div>

          <label className="flex h-10 w-full items-center gap-3 rounded-md border border-slate-200 bg-slate-50 px-3 md:max-w-[340px]">
            <Search size={16} className="text-slate-400" />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search title, type, status, run"
              className="h-full min-w-0 flex-1 bg-transparent text-[14px] text-slate-700 outline-none placeholder:text-slate-400"
            />
          </label>
        </div>

        {loading && (
          <div className="px-6 py-12 text-center text-[14px] text-slate-500">
            Loading incidents...
          </div>
        )}

        {!loading && filteredIncidents.length === 0 && (
          <div className="px-6 py-14 text-center">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-md border border-slate-200 bg-slate-50 text-slate-400">
              <CheckCircle2 size={22} />
            </div>
            <h3 className="mt-4 text-[17px] font-semibold text-slate-950">
              All clear
            </h3>
            <p className="mx-auto mt-2 max-w-[420px] text-[14px] leading-6 text-slate-500">
              No matching incidents need attention right now.
            </p>
          </div>
        )}

        {!loading && filteredIncidents.length > 0 && (
          <div className="divide-y divide-slate-200">
            {groupedRuns.map((run) => {
              const severity = getSeverityMeta(run.severity);
              const SeverityIcon = severity.icon;

              return (
                <article
                  key={run.runId}
                  className="grid gap-4 px-5 py-4 transition hover:bg-slate-50/70 lg:grid-cols-[150px_minmax(280px,1fr)_160px_130px_170px_130px]"
                >
                  <div>
                    <span
                      className={`inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-[12px] font-semibold capitalize ${severity.className}`}
                    >
                      <SeverityIcon size={14} />
                      {run.severity || "Unknown"}
                    </span>
                  </div>

                  <div className="min-w-0">
                    <h3 className="truncate text-[15px] font-semibold text-slate-950">
                      Run #{run.runId}
                    </h3>
                    <p className="mt-1 truncate text-[12px] text-slate-500">
                      {run.incidents.length} incidents, {run.open} open, {run.resolved} resolved
                    </p>
                  </div>

                  <div>
                    <div className="text-[11px] font-medium text-slate-500 lg:hidden">
                      Incident count
                    </div>
                    <span className="mt-1 inline-flex rounded-md border border-slate-200 bg-slate-50 px-2.5 py-1 font-mono text-[12px] font-semibold text-slate-700 lg:mt-0">
                      {run.incidents.length}
                    </span>
                  </div>

                  <div>
                    <div className="text-[11px] font-medium text-slate-500 lg:hidden">
                      Status
                    </div>
                    <span
                      className={`mt-1 inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-[12px] font-semibold lg:mt-0 ${
                        run.open === 0
                          ? "border-slate-200 bg-slate-50 text-slate-600"
                          : "border-red-200 bg-red-50 text-red-700"
                      }`}
                    >
                      <span
                        className={`h-1.5 w-1.5 rounded-full ${
                          run.open === 0 ? "bg-slate-400" : "bg-red-500"
                        }`}
                      />
                      {run.open === 0 ? "Resolved" : `${run.open} open`}
                    </span>
                  </div>

                  <div className="text-[12px] text-slate-600">
                    <div className="text-[11px] font-medium text-slate-500 lg:hidden">
                      Last detected
                    </div>
                    <span>{formatDate(run.latestAt)}</span>
                  </div>

                  <div className="flex items-center justify-end">
                    <button
                      onClick={() => setSelectedRunId(run.runId)}
                      className="inline-flex items-center gap-2 rounded-md border border-slate-200 bg-white px-3 py-2 text-[12px] font-semibold text-slate-700 transition hover:border-blue-200 hover:bg-blue-50 hover:text-blue-700"
                    >
                      <Eye size={14} />
                      View details
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>

      {selectedRun && (
        <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/30 backdrop-blur-sm">
          <button
            type="button"
            aria-label="Close details backdrop"
            className="absolute inset-0 cursor-default"
            onClick={() => setSelectedRunId(null)}
          />
          <aside className="relative flex h-full w-full max-w-5xl flex-col border-l border-slate-200 bg-white shadow-[0_24px_80px_rgba(15,23,42,0.25)]">
            <div className="flex items-start justify-between border-b border-slate-200 px-6 py-5">
              <div>
                <h3 className="text-[18px] font-semibold text-slate-950">
                  Run #{selectedRun.runId} incident details
                </h3>
                <p className="mt-1 text-[13px] text-slate-500">
                  {selectedRun.incidents.length} incidents, {selectedRun.open} open, {selectedRun.resolved} resolved
                </p>
              </div>
              <button
                onClick={() => setSelectedRunId(null)}
                className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-slate-200 text-slate-500 transition hover:bg-slate-50 hover:text-slate-900"
                aria-label="Close details"
              >
                <X size={16} />
              </button>
            </div>

            <div className="grid gap-4 border-b border-slate-200 bg-slate-50 px-6 py-4 md:grid-cols-3">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">
                  Incidents
                </p>
                <p className="mt-1 text-[22px] font-semibold text-slate-950">
                  {selectedRun.incidents.length}
                </p>
              </div>
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">
                  Open
                </p>
                <p className="mt-1 text-[22px] font-semibold text-red-600">
                  {selectedRun.open}
                </p>
              </div>
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">
                  Resolved
                </p>
                <p className="mt-1 text-[22px] font-semibold text-slate-950">
                  {selectedRun.resolved}
                </p>
              </div>
            </div>

            <div className="min-h-0 flex-1 overflow-auto p-6">
              <div className="mb-4 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                <div>
                  <p className="text-[14px] font-semibold text-slate-900">
                    RCA triage summary
                  </p>
                  <p className="mt-1 text-[13px] leading-5 text-slate-500">
                    Incidents are escalated signals created from drift, quality, and schema failures.
                  </p>
                </div>
                <a
                  href={`/pipelines?run=${selectedRun.runId}`}
                  className="inline-flex items-center gap-2 rounded-md border border-slate-200 bg-white px-3 py-2 text-[12px] font-semibold text-blue-700 transition hover:bg-slate-50"
                >
                  <ExternalLink size={14} />
                  Open pipeline
                </a>
              </div>

              <div className="mb-6 grid gap-3 lg:grid-cols-3">
                {buildIncidentRunSummary(selectedRun).map((item) => (
                  <div
                    key={item.label}
                    className="rounded-md border border-slate-200 bg-slate-50 p-4"
                  >
                    <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">
                      {item.label}
                    </p>
                    <p className="mt-2 text-[15px] font-semibold leading-6 text-slate-950">
                      {item.value}
                    </p>
                    <p className="mt-1 text-[12px] leading-5 text-slate-500">
                      {item.detail}
                    </p>
                  </div>
                ))}
              </div>

              <div className="mb-4">
                {agentLoading ? (
                  <div className="rounded-xl border border-slate-200 bg-white p-5 text-center text-[13px] text-slate-400">
                    Loading agent trace...
                  </div>
                ) : shouldShowLiveTrace ? (
                  <AgentTraceStepper
                    steps={wsSteps}
                    isLive={isLive && liveTraceRunId === selectedRunIdLabel}
                  />
                ) : displayAgentSteps.length > 0 ? (
                  <AgentTraceStepper steps={displayAgentSteps} isLive={false} />
                ) : (
                  <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50 p-5 text-center">
                    <p className="text-[13px] font-medium text-slate-500">AI Agent Trace</p>
                    <p className="mt-1 text-[12px] text-slate-400">
                      No trace data yet. The AI agent will generate this when it processes the next pipeline run.
                    </p>
                  </div>
                )}
              </div>

              {shouldShowRcaReport && (
                <div className="mb-6">
                  <IncidentReasoningCard
                    rcaReport={selectedRcaReport}
                    guidance={selectedRcaIncident?.guidance}
                    agentRuns={agentRuns}
                  />
                </div>
              )}

              {selectedRcaReport && !shouldShowRcaReport && (
                <div className="mb-6 rounded-xl border border-slate-200 bg-slate-50 px-5 py-4">
                  <p className="text-[13px] font-semibold text-slate-800">
                    AI Root Cause Analysis
                  </p>
                  <p className="mt-1 text-[12px] leading-5 text-slate-500">
                    The report will appear here after the reporting step finishes saving the final RCA output.
                  </p>
                </div>
              )}

              <div className="overflow-hidden rounded-md border border-slate-200 bg-white">
                <div className="grid gap-4 border-b border-slate-200 bg-slate-50 px-4 py-3 text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500 lg:grid-cols-[150px_minmax(280px,1fr)_160px_130px_170px]">
                  <span>Severity</span>
                  <span>Incident</span>
                  <span>Type</span>
                  <span>Status</span>
                  <span className="text-right">Created At</span>
                </div>
                {selectedRun.incidents.map((incident) => {
                  const severity = getSeverityMeta(incident.severity);
                  const SeverityIcon = severity.icon;
                  const resolved = isResolved(incident.status);
                  const guidance = getIncidentGuidance(incident);
                  const hasDedicatedRcaCard = Boolean(incident.rca_report);

                  return (
                    <div
                      key={incident.id}
                      className="border-b border-slate-200 px-4 py-3 last:border-b-0"
                    >
                      <div className="grid gap-4 lg:grid-cols-[150px_minmax(280px,1fr)_160px_130px_170px]">
                        <div>
                          <span
                            className={`inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-[12px] font-semibold capitalize ${severity.className}`}
                          >
                            <SeverityIcon size={14} />
                            {incident.severity || "Unknown"}
                          </span>
                        </div>

                        <div className="min-w-0">
                          <h4 className="truncate text-[14px] font-semibold text-slate-950">
                            {incident.title || "Untitled incident"}
                          </h4>
                          <p
                            className="mt-1 text-[12px] text-slate-500"
                            title={incident.description}
                          >
                            {incident.description || "No incident description available."}
                          </p>
                        </div>

                        <span className="inline-flex h-fit rounded-md border border-slate-200 bg-slate-50 px-2.5 py-1 font-mono text-[12px] font-semibold text-slate-700">
                          {humanizeType(incident.failure_type)}
                        </span>

                        <span
                          className={`inline-flex h-fit items-center gap-1.5 rounded-md border px-2.5 py-1 text-[12px] font-semibold ${
                            resolved
                              ? "border-slate-200 bg-slate-50 text-slate-600"
                              : "border-red-200 bg-red-50 text-red-700"
                          }`}
                        >
                          <span
                            className={`h-1.5 w-1.5 rounded-full ${resolved ? "bg-slate-400" : "bg-red-500"}`}
                          />
                          {incident.status || "Open"}
                        </span>

                        <div className="flex items-center gap-2 text-[12px] font-medium text-slate-500 lg:justify-end">
                          <Clock3 size={14} />
                          {formatDate(incident.created_at)}
                        </div>
                      </div>

                      {!hasDedicatedRcaCard && (
                        <div className="mt-3 grid gap-3 rounded-md border border-slate-200 bg-slate-50 p-3 lg:grid-cols-2">
                          <div>
                            <p className="text-[12px] font-semibold text-slate-800">Likely cause</p>
                            <p className="mt-1 text-[12px] leading-5 text-slate-600">
                              {guidance.cause}
                            </p>
                            {guidance.source && (
                              <p className="mt-1 font-mono text-[11px] text-slate-500">
                                {guidance.source}
                                {guidance.model ? ` / ${guidance.model}` : ""}
                              </p>
                            )}
                          </div>
                          <div>
                            <p className="text-[12px] font-semibold text-blue-800">Next action</p>
                            <p className="mt-1 text-[12px] leading-5 text-blue-900">
                              {guidance.action}
                            </p>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </aside>
        </div>
      )}
    </div>
  );
}
