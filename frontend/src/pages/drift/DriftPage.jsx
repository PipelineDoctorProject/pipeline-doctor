import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  BarChart2,
  Info,
  RefreshCw,
  Search,
  ShieldAlert,
} from "lucide-react";

import { getDriftFindings } from "../../store/driftStore";

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
  const [findings, setFindings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState("");

  async function loadFindings() {
    try {
      setLoading(true);
      const data = await getDriftFindings();
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
  }, []);

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
              Drift Findings
            </h2>
            <p className="mt-1 text-[13px] text-slate-500">
              Detailed metrics behind the charts.
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
              Drift metrics will appear after pipeline runs are processed.
            </p>
          </div>
        )}

        {!loading && filteredFindings.length > 0 && (
          <div className="divide-y divide-slate-200">
            {filteredFindings.map((finding) => (
              <article
                key={finding.id}
                className="grid gap-4 px-5 py-4 transition hover:bg-slate-50/70 lg:grid-cols-[140px_minmax(220px,1fr)_150px_140px_170px_110px]"
              >
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
                  <h3 className="truncate text-[15px] font-semibold text-slate-950">
                    {finding.feature_name || "Unknown feature"}
                  </h3>
                  <p className="mt-1 text-[12px] text-slate-500">
                    Drift detected: {finding.drift_detected ? "Yes" : "No"}
                  </p>
                </div>

                <div>
                  <div className="text-[11px] font-medium text-slate-500 lg:hidden">
                    Drift score
                  </div>
                  <span className="mt-1 inline-flex rounded-md border border-slate-200 bg-slate-50 px-2.5 py-1 font-mono text-[12px] font-semibold text-slate-700 lg:mt-0">
                    {formatNumber(finding.drift_score)}
                  </span>
                </div>

                <div>
                  <div className="text-[11px] font-medium text-slate-500 lg:hidden">
                    PSI
                  </div>
                  <span className="mt-1 inline-flex rounded-md border border-slate-200 bg-white px-2.5 py-1 font-mono text-[12px] font-semibold text-slate-700 lg:mt-0">
                    {formatNumber(finding.psi_score, 4)}
                  </span>
                </div>

                <div className="text-[12px] text-slate-600">
                  <div>
                    KS:{" "}
                    <span className="font-mono font-semibold">
                      {formatNumber(finding.ks_score, 4)}
                    </span>
                  </div>
                  <div>
                    p-value:{" "}
                    <span className="font-mono font-semibold">
                      {formatNumber(finding.ks_pvalue, 4)}
                    </span>
                  </div>
                </div>

                <a
                  href={`/pipelines?run=${finding.run_id}`}
                  className="inline-flex rounded-md border border-slate-200 bg-white px-2.5 py-1 text-[12px] font-semibold text-blue-700 transition hover:bg-slate-50 lg:justify-center"
                >
                  #{finding.run_id || "-"}
                </a>
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
