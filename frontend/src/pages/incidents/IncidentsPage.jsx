import { useEffect, useMemo, useState } from "react";
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  Clock3,
  Info,
  RefreshCw,
  Search,
  ShieldAlert,
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

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");

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
              Incident Queue
            </h2>
            <p className="mt-1 text-[13px] text-slate-500">
              Review current incident context and affected pipeline runs.
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
            {filteredIncidents.map((incident) => {
              const severity = getSeverityMeta(incident.severity);
              const SeverityIcon = severity.icon;
              const resolved = isResolved(incident.status);

              return (
                <article
                  key={incident.id}
                  className="grid gap-4 px-5 py-4 transition hover:bg-slate-50/70 lg:grid-cols-[150px_minmax(280px,1fr)_160px_130px_130px_170px]"
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
                    <h3 className="truncate text-[15px] font-semibold text-slate-950">
                      {incident.title || "Untitled incident"}
                    </h3>
                    <p
                      className="mt-1 truncate text-[12px] text-slate-500"
                      title={incident.description}
                    >
                      {incident.description || "No incident description available."}
                    </p>
                  </div>

                  <div>
                    <div className="text-[11px] font-medium text-slate-500 lg:hidden">
                      Type
                    </div>
                    <span className="mt-1 inline-flex rounded-md border border-slate-200 bg-slate-50 px-2.5 py-1 font-mono text-[12px] font-semibold text-slate-700 lg:mt-0">
                      {incident.failure_type || "unknown"}
                    </span>
                  </div>

                  <div>
                    <div className="text-[11px] font-medium text-slate-500 lg:hidden">
                      Status
                    </div>
                    <span
                      className={`mt-1 inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-[12px] font-semibold lg:mt-0 ${
                        resolved
                          ? "border-slate-200 bg-slate-50 text-slate-600"
                          : "border-red-200 bg-red-50 text-red-700"
                      }`}
                    >
                      <span
                        className={`h-1.5 w-1.5 rounded-full ${
                          resolved ? "bg-slate-400" : "bg-red-500"
                        }`}
                      />
                      {incident.status || "Open"}
                    </span>
                  </div>

                  <div>
                    <div className="text-[11px] font-medium text-slate-500 lg:hidden">
                      Run ID
                    </div>
                    <a
                      href={`/pipelines?run=${incident.run_id}`}
                      className="mt-1 inline-flex rounded-md border border-slate-200 bg-white px-2.5 py-1 text-[12px] font-semibold text-blue-700 transition hover:bg-slate-50 lg:mt-0"
                    >
                      #{incident.run_id || "-"}
                    </a>
                  </div>

                  <div className="flex items-center gap-2 text-[12px] font-medium text-slate-500 lg:justify-end">
                    <Clock3 size={14} />
                    {formatDate(incident.created_at)}
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
