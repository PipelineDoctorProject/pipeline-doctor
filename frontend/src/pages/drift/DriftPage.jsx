import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  BarChart2,
  Eye,
  ExternalLink,
  Info,
  RefreshCw,
  Search,
  ShieldAlert,
  X,
} from "lucide-react";

import { getDriftFindings, getDriftFindingsByRun } from "../../store/driftStore";
import { useSearchParams } from "react-router-dom";
import useSelectedModelStore from "../../store/selectedModelStore";

const severityStyles = {
  critical: "border-red-200 bg-red-50 text-red-700",
  high: "border-orange-200 bg-orange-50 text-orange-700",
  medium: "border-amber-200 bg-amber-50 text-amber-700",
  low: "border-blue-200 bg-blue-50 text-blue-700",
};

const severityColors = {
  critical: "#dc2626",
  high: "#ea580c",
  medium: "#d97706",
  low: "#2563eb",
  unknown: "#64748b",
};

const featurePalette = [
  "#0b2442",
  "#2563eb",
  "#0891b2",
  "#16a34a",
  "#d97706",
  "#dc2626",
  "#7c3aed",
  "#475569",
];

function formatNumber(value, digits = 3) {
  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(digits) : "N/A";
}

function getSeverityClass(severity) {
  return (
    severityStyles[String(severity || "").toLowerCase()] ||
    "border-slate-200 bg-slate-50 text-slate-700"
  );
}

function getSeverityRank(severity) {
  const ranks = { critical: 4, high: 3, medium: 2, low: 1 };
  return ranks[String(severity || "").toLowerCase()] || 0;
}

function getWorstSeverity(findings) {
  return findings.reduce((worst, finding) => {
    return getSeverityRank(finding.severity) > getSeverityRank(worst)
      ? finding.severity
      : worst;
  }, "low");
}

function getDriftInterpretation(finding) {
  if (finding.interpretation?.title || finding.interpretation?.cause) {
    return {
      title: finding.interpretation.title || `${finding.feature_name || "Feature"} drift interpretation`,
      cause: finding.interpretation.cause || "No drift cause was returned.",
      action: finding.interpretation.action || "Review the related batch and baseline data.",
    };
  }

  const psi = Number(finding.psi_score);
  const ksPvalue = Number(finding.ks_pvalue);
  const feature = finding.feature_name || "Feature";

  if (!finding.drift_detected) {
    return {
      title: `${feature} is stable`,
      cause: "The current distribution is close enough to the baseline population.",
      action: "Keep monitoring future runs.",
    };
  }

  const strength = Number.isFinite(psi)
    ? psi >= 0.3
      ? "strong"
      : psi >= 0.2
        ? "moderate"
        : "minor"
    : "detected";

  const significance = Number.isFinite(ksPvalue) && ksPvalue < 0.05
    ? "The KS p-value also supports a statistically significant shift."
    : "The KS p-value is not strongly significant, so treat this as a monitoring signal and confirm with business context.";

  return {
    title: `${feature} shows ${strength} population drift`,
    cause: `${feature} no longer follows the baseline distribution. This can come from source changes, seasonality, traffic mix changes, or a stale baseline. ${significance}`,
    action: "Compare the current batch source and time window with the baseline. Refresh the baseline or retrain only if the new population is expected.",
  };
}

function buildRunDriftSummary(run) {
  if (!run) return [];

  const drifting = run.findings.filter((finding) => finding.drift_detected);
  const stable = run.findings.length - drifting.length;
  const strongest = [...drifting].sort(
    (a, b) => Number(b.drift_score || 0) - Number(a.drift_score || 0),
  )[0];

  return [
    {
      label: "Primary signal",
      value: drifting.length
        ? `${drifting.length} feature${drifting.length === 1 ? "" : "s"} drifted`
        : "No drifted features",
      detail: stable > 0 ? `${stable} feature${stable === 1 ? "" : "s"} remained stable.` : "All tracked features drifted in this run.",
    },
    {
      label: "Strongest feature",
      value: strongest?.feature_name || "Not available",
      detail: strongest
        ? `Drift score ${formatNumber(strongest.drift_score)}, PSI ${formatNumber(strongest.psi_score, 4)}.`
        : "No drift signal exceeded the configured threshold.",
    },
    {
      label: "RCA guidance",
      value: run.severity === "critical" ? "Investigate before relying on predictions" : "Review as monitoring context",
      detail: "Use this with Data Quality findings to decide whether the issue is data corruption, expected population change, or baseline staleness.",
    },
  ];
}

function groupFindingsByRun(findings) {
  return Array.from(
    findings
      .reduce((groups, finding) => {
        const runId = finding.run_id || "unknown";
        const group = groups.get(runId) || {
          runId,
          findings: [],
          drifted: 0,
          maxScore: 0,
          severity: "low",
          latestAt: null,
        };

        group.findings.push(finding);
        if (finding.drift_detected) group.drifted += 1;
        group.maxScore = Math.max(group.maxScore, Number(finding.drift_score || 0));
        group.severity = getWorstSeverity(group.findings);

        if (finding.created_at) {
          const currentTime = new Date(finding.created_at).getTime();
          const latestTime = group.latestAt ? new Date(group.latestAt).getTime() : 0;
          if (Number.isFinite(currentTime) && currentTime > latestTime) {
            group.latestAt = finding.created_at;
          }
        }

        groups.set(runId, group);
        return groups;
      }, new Map())
      .values(),
  ).sort((a, b) => Number(b.runId) - Number(a.runId));
}

function formatDate(value) {
  if (!value) return "Not available";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Not available";

  return date.toLocaleString(undefined, {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function DistributionBars({ counts, total }) {
  const rows = ["critical", "high", "medium", "low"];

  return (
    <div className="space-y-3">
      {rows.map((severity) => {
        const value = counts[severity] || 0;
        const width = total ? Math.max((value / total) * 100, value ? 8 : 0) : 0;

        return (
          <div key={severity}>
            <div className="mb-1 flex items-center justify-between text-[12px]">
              <span className="font-medium capitalize text-slate-600">
                {severity}
              </span>
              <span className="font-semibold text-slate-950">{value}</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-slate-100">
              <div
                className="h-full rounded-full"
                style={{
                  width: `${width}%`,
                  backgroundColor: severityColors[severity],
                }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

function DriftScoreChart({ findings }) {
  const numericFindings = findings.filter((finding) =>
    Number.isFinite(Number(finding.drift_score)),
  );

  const featureNames = Array.from(
    new Set(
      numericFindings.map(
        (finding) => finding.feature_name || "Unknown feature",
      ),
    ),
  ).slice(0, 8);

  const runGroups = Array.from(
    numericFindings
      .reduce((groups, finding) => {
        const runId = finding.run_id || "Unknown";
        const featureName = finding.feature_name || "Unknown feature";

        if (!featureNames.includes(featureName)) return groups;

        const currentGroup = groups.get(runId) || {
          runId,
          values: {},
        };

        currentGroup.values[featureName] = Number(finding.drift_score);
        groups.set(runId, currentGroup);

        return groups;
      }, new Map())
      .values(),
  ).slice(0, 8);

  if (runGroups.length === 0 || featureNames.length === 0) {
    return (
      <div className="flex min-h-[240px] items-center justify-center rounded-md border border-dashed border-slate-200 bg-slate-50 text-[13px] text-slate-500">
        Drift scores will appear here after pipeline runs produce findings.
      </div>
    );
  }

  const maxScore = Math.max(
    1,
    ...runGroups.flatMap((group) => Object.values(group.values)),
  );
  const chartHeight = 180;

  return (
    <div>
      <div className="overflow-x-auto">
        <div className="min-w-[760px]">
          <div className="mb-4 flex flex-wrap gap-3">
            {featureNames.map((featureName, index) => (
              <div
                key={featureName}
                className="flex items-center gap-2 text-[11px] font-medium text-slate-600"
              >
                <span
                  className="h-2.5 w-2.5 rounded-full"
                  style={{
                    backgroundColor:
                      featurePalette[index % featurePalette.length],
                  }}
                />
                <span className="max-w-[140px] truncate">{featureName}</span>
              </div>
            ))}
          </div>

          <div className="flex h-[240px] items-end gap-5 border-b border-l border-slate-200 px-4 pb-4">
            {runGroups.map((group) => (
              <div
                key={group.runId}
                className="flex min-w-[92px] flex-1 flex-col items-center justify-end gap-2"
              >
                <div className="flex h-[190px] w-full items-end justify-center gap-1.5">
                  {featureNames.map((featureName, index) => {
                    const score = group.values[featureName] || 0;
                    const barHeight = score
                      ? Math.max((score / maxScore) * chartHeight, 6)
                      : 0;

                    return (
                      <div
                        key={`${group.runId}-${featureName}`}
                        className="group flex h-full flex-1 items-end justify-center"
                        title={`Run #${group.runId} / ${featureName}: ${formatNumber(
                          score,
                        )}`}
                      >
                        <div
                          className="w-full max-w-[18px] rounded-t-sm transition group-hover:opacity-80"
                          style={{
                            height: `${barHeight}px`,
                            backgroundColor:
                              featurePalette[index % featurePalette.length],
                          }}
                        />
                      </div>
                    );
                  })}
                </div>
                <span className="w-full truncate text-center text-[11px] font-semibold text-slate-600">
                  Run #{group.runId}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-3 flex items-center justify-between text-[11px] text-slate-500">
        <span>
          Grouped by run ID / {featureNames.length} column
          {featureNames.length === 1 ? "" : "s"}
        </span>
        <span>Max score {formatNumber(maxScore)}</span>
      </div>
    </div>
  );
}

export default function DriftPage() {
  const [searchParams] = useSearchParams();
  const runParam = searchParams.get("run");
  const [findings, setFindings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [selectedRunId, setSelectedRunId] = useState(runParam);
  const selectedModelId = useSelectedModelStore((state) => state.selectedModelId);

  async function loadFindings() {
    try {
      setLoading(true);
      const data = runParam
        ? await getDriftFindingsByRun(runParam)
        : await getDriftFindings(selectedModelId);
      setFindings(data || []);
    } catch (err) {
      console.log(err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadFindings();
  }, [runParam, selectedModelId]);

  const filteredFindings = useMemo(() => {
    const needle = query.trim().toLowerCase();
    if (!needle) return findings;

    return findings.filter((finding) =>
      [
        finding.feature_name,
        finding.severity,
        finding.run_id,
        finding.drift_score,
        finding.psi_score,
      ]
        .filter(Boolean)
        .join(" ")
        .toLowerCase()
        .includes(needle),
    );
  }, [findings, query]);

  const driftCount = findings.filter((finding) => finding.drift_detected).length;
  const averageScore =
    findings.length === 0
      ? 0
      : findings.reduce(
          (sum, finding) => sum + Number(finding.drift_score || 0),
          0,
        ) / findings.length;

  const severityCounts = findings.reduce((counts, finding) => {
    const severity = String(finding.severity || "unknown").toLowerCase();
    return {
      ...counts,
      [severity]: (counts[severity] || 0) + 1,
    };
  }, {});

  const groupedRuns = useMemo(
    () => groupFindingsByRun(filteredFindings),
    [filteredFindings],
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
              Drift Detection
            </h1>
            <p className="mt-2 text-[14px] leading-6 text-slate-500">
              Track drift findings from production pipeline runs using real PSI,
              KS, and drift score data.
            </p>
          </div>

          <button
            onClick={loadFindings}
            className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-slate-950 px-4 text-[13px] font-semibold text-white transition hover:bg-slate-800"
          >
            <RefreshCw size={15} />
            Refresh Analysis
          </button>
        </div>

        <div className="grid border-b border-slate-200 md:grid-cols-3">
          <div className="border-b border-slate-200 px-6 py-4 md:border-b-0 md:border-r">
            <div className="flex items-center justify-between text-[12px] font-medium text-slate-500">
              Findings
              <Activity size={16} />
            </div>
            <div className="mt-2 text-[26px] font-semibold text-slate-950">
              {findings.length}
            </div>
          </div>

          <div className="border-b border-slate-200 px-6 py-4 md:border-b-0 md:border-r">
            <div className="flex items-center justify-between text-[12px] font-medium text-slate-500">
              Features drifting
              <ShieldAlert size={16} />
            </div>
            <div className="mt-2 text-[26px] font-semibold text-slate-950">
              {driftCount}
            </div>
          </div>

          <div className="px-6 py-4">
            <div className="flex items-center justify-between text-[12px] font-medium text-slate-500">
              Avg drift score
              <BarChart2 size={16} />
            </div>
            <div className="mt-2 text-[26px] font-semibold text-slate-950">
              {formatNumber(averageScore)}
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_340px]">
        <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-[0_12px_34px_rgba(15,23,42,0.04)]">
          <div className="mb-5 flex items-center justify-between">
            <div>
              <h2 className="text-[16px] font-semibold text-slate-950">
                Column Drift by Run
              </h2>
              <p className="mt-1 text-[13px] text-slate-500">
                Each run is a group; each colored bar is a drifted column.
              </p>
            </div>
            <BarChart2 size={18} className="text-slate-400" />
          </div>

          <DriftScoreChart findings={filteredFindings} />
        </div>

        <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-[0_12px_34px_rgba(15,23,42,0.04)]">
          <div className="mb-5 flex items-center justify-between">
            <div>
              <h2 className="text-[16px] font-semibold text-slate-950">
                Severity Mix
              </h2>
              <p className="mt-1 text-[13px] text-slate-500">
                Distribution from current findings.
              </p>
            </div>
            <AlertTriangle size={18} className="text-slate-400" />
          </div>

          <DistributionBars counts={severityCounts} total={findings.length} />
        </div>
      </section>

      <section className="rounded-lg border border-slate-200 bg-white shadow-[0_12px_34px_rgba(15,23,42,0.04)]">
        <div className="flex flex-col gap-4 border-b border-slate-200 px-5 py-4 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-[16px] font-semibold text-slate-950">
              Drift Runs
            </h2>
            <p className="mt-1 text-[13px] text-slate-500">
              Use View details to inspect the column-level findings for a run.
            </p>
          </div>

          <label className="flex h-10 w-full items-center gap-3 rounded-md border border-slate-200 bg-slate-50 px-3 md:max-w-[340px]">
            <Search size={16} className="text-slate-400" />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search feature, severity, run"
              className="h-full min-w-0 flex-1 bg-transparent text-[14px] text-slate-700 outline-none placeholder:text-slate-400"
            />
          </label>
        </div>

        {loading && (
          <div className="px-6 py-12 text-center text-[14px] text-slate-500">
            Loading drift analysis...
          </div>
        )}

        {!loading && filteredFindings.length === 0 && (
          <div className="px-6 py-14 text-center">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-md border border-slate-200 bg-slate-50 text-slate-400">
              <Activity size={22} />
            </div>
            <h3 className="mt-4 text-[17px] font-semibold text-slate-950">
              No drift findings
            </h3>
            <p className="mx-auto mt-2 max-w-[420px] text-[14px] leading-6 text-slate-500">
              {runParam
                ? `No drift findings were stored for run #${runParam}.`
                : "Drift metrics will appear after pipeline runs are processed."}
            </p>
            {!runParam && selectedModelId !== "all" && (
              <p className="mx-auto mt-2 max-w-[420px] font-mono text-[12px] text-slate-400">
                Selected model id: {selectedModelId}
              </p>
            )}
          </div>
        )}

        {!loading && filteredFindings.length > 0 && (
          <div className="divide-y divide-slate-200">
            {groupedRuns.map((run) => (
              <article
                key={run.runId}
                className="grid gap-4 px-5 py-4 transition hover:bg-slate-50/70 lg:grid-cols-[140px_minmax(220px,1fr)_150px_140px_170px_130px]"
              >
                <div>
                  <span
                    className={`inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-[12px] font-semibold capitalize ${getSeverityClass(
                      run.severity,
                    )}`}
                  >
                    <Info size={14} />
                    {run.severity || "Low"}
                  </span>
                </div>

                <div className="min-w-0">
                  <h3 className="truncate text-[15px] font-semibold text-slate-950">
                    Run #{run.runId}
                  </h3>
                  <p className="mt-1 text-[12px] text-slate-500">
                    {run.findings.length} findings, {run.drifted} drifting features
                  </p>
                </div>

                <div>
                  <div className="text-[11px] font-medium text-slate-500 lg:hidden">
                    Max drift score
                  </div>
                  <span className="mt-1 inline-flex rounded-md border border-slate-200 bg-slate-50 px-2.5 py-1 font-mono text-[12px] font-semibold text-slate-700 lg:mt-0">
                    {formatNumber(run.maxScore)}
                  </span>
                </div>

                <div>
                  <div className="text-[11px] font-medium text-slate-500 lg:hidden">
                    Run ID
                  </div>
                  <span className="mt-1 inline-flex rounded-md border border-slate-200 bg-white px-2.5 py-1 text-[12px] font-semibold text-blue-700 lg:mt-0">
                    #{run.runId}
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
            ))}
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
                  Run #{selectedRun.runId} drift details
                </h3>
                <p className="mt-1 text-[13px] text-slate-500">
                  {selectedRun.findings.length} findings, {selectedRun.drifted} drifting features, max score {formatNumber(selectedRun.maxScore)}
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
                <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">Findings</p>
                <p className="mt-1 text-[22px] font-semibold text-slate-950">{selectedRun.findings.length}</p>
              </div>
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">Drifting features</p>
                <p className="mt-1 text-[22px] font-semibold text-orange-600">{selectedRun.drifted}</p>
              </div>
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">Max score</p>
                <p className="mt-1 text-[22px] font-semibold text-slate-950">{formatNumber(selectedRun.maxScore)}</p>
              </div>
            </div>

            <div className="min-h-0 flex-1 overflow-auto p-6">
              <div className="mb-4 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                <div>
                  <p className="text-[14px] font-semibold text-slate-900">
                    Root-cause context
                  </p>
                  <p className="mt-1 text-[13px] leading-5 text-slate-500">
                    Drift signals explain population changes. Compare them with data quality and incident pages for the full RCA.
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
                {buildRunDriftSummary(selectedRun).map((item) => (
                  <div key={item.label} className="rounded-md border border-slate-200 bg-slate-50 p-4">
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

              <div className="overflow-hidden rounded-md border border-slate-200 bg-white">
                <div className="grid gap-4 border-b border-slate-200 bg-slate-50 px-4 py-3 text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500 lg:grid-cols-[140px_minmax(220px,1fr)_150px_140px_170px]">
                  <span>Severity</span>
                  <span>Feature</span>
                  <span>Drift Score</span>
                  <span>PSI</span>
                  <span>KS / p-value</span>
                </div>
                {selectedRun.findings.map((finding) => {
                  const interpretation = getDriftInterpretation(finding);

                  return (
                    <div
                      key={finding.id}
                      className="border-b border-slate-200 px-4 py-3 last:border-b-0"
                    >
                      <div className="grid gap-4 lg:grid-cols-[140px_minmax(220px,1fr)_150px_140px_170px]">
                        <div>
                          <span
                            className={`inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-[12px] font-semibold capitalize ${getSeverityClass(
                              finding.severity,
                            )}`}
                          >
                            <Info size={14} />
                            {finding.severity || "Low"}
                          </span>
                        </div>

                        <div className="min-w-0">
                          <h4 className="truncate text-[14px] font-semibold text-slate-950">
                            {finding.feature_name || "Unknown feature"}
                          </h4>
                          <p className="mt-1 text-[12px] text-slate-500">
                            Drift detected: {finding.drift_detected ? "Yes" : "No"}
                          </p>
                        </div>

                        <span className="inline-flex h-fit rounded-md border border-slate-200 bg-slate-50 px-2.5 py-1 font-mono text-[12px] font-semibold text-slate-700">
                          Score {formatNumber(finding.drift_score)}
                        </span>

                        <span className="inline-flex h-fit rounded-md border border-slate-200 bg-white px-2.5 py-1 font-mono text-[12px] font-semibold text-slate-700">
                          PSI {formatNumber(finding.psi_score, 4)}
                        </span>

                        <div className="text-[12px] text-slate-600">
                          <div>
                            KS: <span className="font-mono font-semibold">{formatNumber(finding.ks_score, 4)}</span>
                          </div>
                          <div>
                            p-value: <span className="font-mono font-semibold">{formatNumber(finding.ks_pvalue, 4)}</span>
                          </div>
                        </div>
                      </div>

                      <div className="mt-3 rounded-md border border-slate-200 bg-slate-50 p-3">
                        <p className="text-[12px] font-semibold text-slate-800">
                          {interpretation.title}
                        </p>
                        <p className="mt-1 text-[12px] leading-5 text-slate-600">
                          {interpretation.cause}
                        </p>
                        <p className="mt-2 text-[12px] font-medium leading-5 text-blue-800">
                          {interpretation.action}
                        </p>
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
