import { useEffect, useMemo, useState } from "react";
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

import { getIncidents } from "../../store/incidentStore";

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

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [selectedRunId, setSelectedRunId] = useState(null);

  async function loadIncidents() {
    try {
      setLoading(true);
      const data = await getIncidents();
      setIncidents(data || []);
    } catch (err) {
      console.log(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadIncidents();
  }, []);

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
            onClick={loadIncidents}
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
                <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">Incidents</p>
                <p className="mt-1 text-[22px] font-semibold text-slate-950">{selectedRun.incidents.length}</p>
              </div>
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">Open</p>
                <p className="mt-1 text-[22px] font-semibold text-red-600">{selectedRun.open}</p>
              </div>
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">Resolved</p>
                <p className="mt-1 text-[22px] font-semibold text-slate-950">{selectedRun.resolved}</p>
              </div>
            </div>

            <div className="min-h-0 flex-1 overflow-auto p-6">
              <div className="mb-4 flex items-center justify-between">
                <p className="text-[13px] font-medium text-slate-500">
                  Incidents raised from this pipeline run.
                </p>
                <a
                  href={`/pipelines?run=${selectedRun.runId}`}
                  className="inline-flex items-center gap-2 rounded-md border border-slate-200 bg-white px-3 py-2 text-[12px] font-semibold text-blue-700 transition hover:bg-slate-50"
                >
                  <ExternalLink size={14} />
                  Open pipeline
                </a>
              </div>

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

                  return (
                    <div
                      key={incident.id}
                      className="grid gap-4 border-b border-slate-200 px-4 py-3 last:border-b-0 lg:grid-cols-[150px_minmax(280px,1fr)_160px_130px_170px]"
                    >
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
                        <p className="mt-1 text-[12px] text-slate-500" title={incident.description}>
                          {incident.description || "No incident description available."}
                        </p>
                      </div>

                      <span className="inline-flex h-fit rounded-md border border-slate-200 bg-slate-50 px-2.5 py-1 font-mono text-[12px] font-semibold text-slate-700">
                        {incident.failure_type || "unknown"}
                      </span>

                      <span
                        className={`inline-flex h-fit items-center gap-1.5 rounded-md border px-2.5 py-1 text-[12px] font-semibold ${
                          resolved
                            ? "border-slate-200 bg-slate-50 text-slate-600"
                            : "border-red-200 bg-red-50 text-red-700"
                        }`}
                      >
                        <span className={`h-1.5 w-1.5 rounded-full ${resolved ? "bg-slate-400" : "bg-red-500"}`} />
                        {incident.status || "Open"}
                      </span>

                      <div className="flex items-center gap-2 text-[12px] font-medium text-slate-500 lg:justify-end">
                        <Clock3 size={14} />
                        {formatDate(incident.created_at)}
                      </div>
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
