import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import {
  Database,
  CheckCircle2,
  XCircle,
  FileSearch,
  Eye,
  ExternalLink,
  X,
  AlertTriangle,
  Info,
  ListChecks,
} from "lucide-react";
import { getDataQualityExplanation, getDataQualityFindings } from "../../store/dataQualityStore";
import useSelectedModelStore from "../../store/selectedModelStore";
import InsightExplanationCard from "../../components/common/InsightExplanationCard";

function formatDate(value) {
  if (!value) return "Not available";
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? "Not available" : date.toLocaleString();
}

function groupFindingsByRun(findings) {
  return Array.from(
    findings
      .reduce((groups, finding) => {
        const runId = finding.pipeline_run_id || "unknown";
        const group = groups.get(runId) || {
          runId,
          findings: [],
          passed: 0,
          failed: 0,
          latestAt: null,
        };

        group.findings.push(finding);
        if (finding.success) group.passed += 1;
        else group.failed += 1;

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

const severityStyles = {
  critical: "border-red-200 bg-red-50 text-red-700",
  high: "border-orange-200 bg-orange-50 text-orange-700",
  medium: "border-amber-200 bg-amber-50 text-amber-700",
  low: "border-slate-200 bg-slate-50 text-slate-600",
};

const severityRank = {
  low: 0,
  medium: 1,
  high: 2,
  critical: 3,
};

const issueCopy = {
  schema_type_mismatch: {
    title: "Column type mismatch",
    severity: "high",
    cause: "The incoming file contains values that do not match the active baseline type, often invalid tokens or formatting changes.",
    action: "Inspect the raw values for the affected column and fix unsafe values upstream before trusting prediction inputs.",
  },
  range: {
    title: "Numeric range violation",
    severity: "medium",
    cause: "The batch contains values outside the baseline profile. This can be a true outlier, a unit change, or a stale baseline.",
    action: "Review rows above or below the baseline limits and decide whether the source data or baseline needs correction.",
  },
  categorical: {
    title: "New category detected",
    severity: "medium",
    cause: "The file contains category values that were not present in the baseline profile.",
    action: "Confirm whether the new values are valid business categories, then update mappings or refresh the baseline if expected.",
  },
  null_ratio: {
    title: "Missing values above threshold",
    severity: "medium",
    cause: "The batch has too many blanks for one or more columns, usually from incomplete extraction or an upstream mapping issue.",
    action: "Check source completeness and joins before relying on imputed values in the cleaned file.",
  },
  extra_columns: {
    title: "Unexpected columns added",
    severity: "medium",
    cause: "A producer added fields, or a newer/wrong file version was uploaded.",
    action: "Approve the schema change only if these fields are expected and downstream consumers are ready.",
  },
  missing_columns: {
    title: "Required columns missing",
    severity: "high",
    cause: "A producer removed or renamed baseline fields that the model or pipeline expects.",
    action: "Restore missing fields or approve a compatible model and baseline before using the batch.",
  },
};

function getSeverityClass(severity) {
  return severityStyles[String(severity || "low").toLowerCase()] || severityStyles.low;
}

function humanizeCheckType(value) {
  return String(value || "check")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function getFindingSeverity(finding) {
  if (finding.success) return "low";
  const checkType = String(finding.check_type || "");
  return issueCopy[checkType]?.severity || "medium";
}

function getFindingMessage(finding) {
  const details = finding.details || {};
  const column = finding.column_name || "Dataset";

  if (finding.check_type === "range") {
    return `${column} observed ${details.observed_min ?? "?"}-${details.observed_max ?? "?"}; baseline expected ${details.baseline_min ?? "?"}-${details.baseline_max ?? "?"}.`;
  }

  if (finding.check_type === "categorical") {
    const unseen = details.unseen_values?.join(", ") || details.info || "unseen values";
    return `${column} contains new value(s): ${unseen}.`;
  }

  if (finding.check_type === "null_ratio") {
    const ratio = details.ratio != null ? `${Math.round(details.ratio * 100)}%` : details.info;
    const threshold = details.threshold != null ? `${Math.round(details.threshold * 100)}%` : "configured threshold";
    return `${column} missing ratio is ${ratio}, threshold is ${threshold}.`;
  }

  if (finding.check_type === "schema_type_mismatch") {
    return details.info || `${column} does not match the expected baseline type.`;
  }

  if (finding.check_type === "extra_columns" || finding.check_type === "missing_columns") {
    return `${humanizeCheckType(finding.check_type)}: ${(details.columns || []).join(", ") || details.info || "No column details"}.`;
  }

  return details.info || "No extra details available.";
}

function buildIssueGroups(findings) {
  const failed = findings.filter((finding) => !finding.success);
  const groups = Array.from(
    failed
      .reduce((map, finding) => {
        const key = finding.check_type || "data_quality";
        const meta = issueCopy[key] || {
          title: humanizeCheckType(key),
          severity: "medium",
          cause: "The incoming batch differs from the active baseline.",
          action: "Inspect the affected rows and compare them against the source contract.",
        };
        const group = map.get(key) || {
          key,
          ...meta,
          findings: [],
          columns: new Set(),
          severity: meta.severity,
        };

        group.findings.push(finding);
        if (finding.column_name) group.columns.add(finding.column_name);
        if (severityRank[getFindingSeverity(finding)] > severityRank[group.severity]) {
          group.severity = getFindingSeverity(finding);
        }

        map.set(key, group);
        return map;
      }, new Map())
      .values(),
  );

  return groups
    .map((group) => ({
      ...group,
      columns: Array.from(group.columns).sort(),
    }))
    .sort((a, b) => severityRank[b.severity] - severityRank[a.severity]);
}

function DetailRows({ details }) {
  if (!details) return <span>No extra details</span>;

  const rows = [
    ["Observed min", details.observed_min],
    ["Observed max", details.observed_max],
    ["Baseline min", details.baseline_min],
    ["Baseline max", details.baseline_max],
    ["Missing count", details.missing_count],
    ["Rows checked", details.row_count],
    ["Unseen count", details.unseen_count],
  ].filter(([, value]) => value !== undefined && value !== null);

  if (details.unseen_values?.length) {
    rows.push(["Unseen values", details.unseen_values.join(", ")]);
  }

  if (details.allowed_values_sample?.length) {
    rows.push(["Allowed sample", details.allowed_values_sample.join(", ")]);
  }

  if (rows.length === 0) {
    return <span>{details.info || JSON.stringify(details)}</span>;
  }

  return (
    <div className="grid gap-1.5">
      {details.info && <p className="text-[12px] leading-5 text-slate-600">{details.info}</p>}
      {rows.map(([label, value]) => (
        <div key={label} className="flex min-w-0 items-start justify-between gap-3 text-[12px] leading-5">
          <span className="shrink-0 text-slate-400">{label}</span>
          <span className="min-w-0 break-words text-right font-medium text-slate-700">{String(value)}</span>
        </div>
      ))}
    </div>
  );
}

export default function DataQualityPage() {
  const [searchParams] = useSearchParams();
  const runParam = searchParams.get("run");
  const [findings, setFindings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedRunId, setSelectedRunId] = useState(runParam);
  const [explanation, setExplanation] = useState(null);
  const [explanationLoading, setExplanationLoading] = useState(false);
  const selectedModelId = useSelectedModelStore((state) => state.selectedModelId);

  // ==========================================
  // LOAD DATA QUALITY FINDINGS
  // ==========================================
  const loadFindings = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getDataQualityFindings(selectedModelId);
      setFindings(data || []);
    } catch (err) {
      console.log(err);
    } finally {
      setLoading(false);
    }
  }, [selectedModelId]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    loadFindings();
  }, [loadFindings]);

  const groupedRuns = useMemo(() => groupFindingsByRun(findings), [findings]);
  const selectedRun = groupedRuns.find((group) => String(group.runId) === String(selectedRunId));
  const selectedIssueGroups = useMemo(
    () => (selectedRun ? buildIssueGroups(selectedRun.findings) : []),
    [selectedRun],
  );

  useEffect(() => {
    if (!selectedRun) return undefined;

    let isActive = true;

    const loadExplanation = async () => {
      try {
        setExplanationLoading(true);
        setExplanation(null);
        const data = await getDataQualityExplanation(selectedRun.runId);
        if (isActive) {
          setExplanation(data);
        }
      } catch (err) {
        console.log(err);
        if (isActive) {
          setExplanation(null);
        }
      } finally {
        if (isActive) {
          setExplanationLoading(false);
        }
      }
    };

    loadExplanation();

    return () => {
      isActive = false;
    };
  }, [selectedRun]);

  return (
    <div className="space-y-5">
      {/* HEADER */}
      <section className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-[0_12px_34px_rgba(15,23,42,0.04)]">
        <div className="flex flex-col gap-5 border-b border-slate-200 px-6 py-5 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h1 className="text-[30px] font-semibold leading-tight text-slate-950">
            Data Quality
          </h1>
          <p className="mt-2 max-w-[720px] text-[14px] leading-6 text-slate-500">
            Monitor the health and integrity of incoming inference data. 
            Review schema validations, missing values, and type mismatches detected during pipeline runs.
          </p>
        </div>
        <button
          onClick={loadFindings}
          className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-slate-950 px-4 text-[13px] font-semibold text-white transition hover:bg-slate-800"
        >
          <Database size={16} />
          Refresh Validations
        </button>
        </div>

        <div className="grid border-b border-slate-200 md:grid-cols-3">
          <div className="border-b border-slate-200 px-6 py-4 md:border-b-0 md:border-r">
            <div className="flex items-center justify-between text-[12px] font-medium text-slate-500">
              Passed checks
              <CheckCircle2 size={16} />
            </div>
            <p className="mt-2 text-[26px] font-semibold text-slate-950">{findings.filter(f => f.success).length}</p>
          </div>
        
          <div className="border-b border-slate-200 px-6 py-4 md:border-b-0 md:border-r">
            <div className="flex items-center justify-between text-[12px] font-medium text-slate-500">
              Failed checks
              <XCircle size={16} />
            </div>
            <p className="mt-2 text-[26px] font-semibold text-slate-950">{findings.filter(f => !f.success).length}</p>
          </div>

          <div className="px-6 py-4">
            <div className="flex items-center justify-between text-[12px] font-medium text-slate-500">
              Total runs
              <FileSearch size={16} />
            </div>
            <p className="mt-2 text-[26px] font-semibold text-slate-950">{groupedRuns.length}</p>
          </div>
        </div>
      </section>

      {/* LOADING STATE */}
      {loading && (
        <div className="rounded-lg border border-slate-200 bg-white p-12 text-center text-[14px] text-slate-500 shadow-[0_12px_34px_rgba(15,23,42,0.04)]">
          Loading Data Quality Findings...
        </div>
      )}

      {/* EMPTY STATE */}
      {!loading && findings.length === 0 && (
        <div className="rounded-lg border border-dashed border-slate-200 bg-white p-16 text-center shadow-[0_12px_34px_rgba(15,23,42,0.04)]">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-md border border-slate-200 bg-slate-50">
            <Database size={28} className="text-gray-400" />
          </div>
          <h3 className="text-[18px] font-semibold text-[#111827]">
            No Validations Found
          </h3>
          <p className="mt-2 text-[14px] text-gray-500 max-w-sm mx-auto">
            Data quality checks will appear here once inference pipelines start processing data.
          </p>
        </div>
      )}

      {/* DATA TABLE */}
      {!loading && findings.length > 0 && (
        <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-[0_12px_34px_rgba(15,23,42,0.04)]">
          
          {/* TABLE TOOLBAR */}
          <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4">
             <h3 className="text-[15px] font-medium text-[#111827]">Recent Validation Runs</h3>
             <span className="text-[12px] font-medium text-slate-500">Grouped by pipeline run</span>
          </div>

          <table className="w-full text-left text-[14px]">
            <thead className="bg-slate-50 text-[12px] font-medium uppercase tracking-[0.1em] text-gray-500">
              <tr>
                <th className="px-6 py-5">Run Health</th>
                <th className="px-6 py-5">Checks</th>
                <th className="px-6 py-5">Failed / Passed</th>
                <th className="px-6 py-5">Run ID</th>
                <th className="px-6 py-5 text-right">Detected At</th>
                <th className="px-6 py-5 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {groupedRuns.map((run) => (
                    <tr
                      key={run.runId}
                      className="group transition hover:bg-slate-50/70"
                    >
                      <td className="px-6 py-5">
                        {run.failed === 0 ? (
                          <div className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium bg-green-50 text-green-700 border border-green-200">
                            <CheckCircle2 size={14} className="mr-1.5" />
                            Passed
                          </div>
                        ) : (
                          <div className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium bg-red-50 text-red-700 border border-red-200">
                            <XCircle size={14} className="mr-1.5" />
                            Needs review
                          </div>
                        )}
                      </td>
                      <td className="px-6 py-5">
                        <span className="font-semibold text-[#111827]">{run.findings.length}</span>
                        <span className="ml-2 text-gray-500">validation checks</span>
                      </td>
                      <td className="px-6 py-5">
                        <span className="font-medium text-red-600">{run.failed} failed</span>
                        <span className="mx-2 text-gray-300">/</span>
                        <span className="font-medium text-green-600">{run.passed} passed</span>
                      </td>
                      <td className="px-6 py-5 text-gray-600">
                        <span className="font-medium text-blue-700">#{run.runId}</span>
                      </td>
                      <td className="px-6 py-5 text-right text-gray-500">
                        <span>{formatDate(run.latestAt)}</span>
                      </td>
                      <td className="px-6 py-5 text-right">
                        <button
                          onClick={() => setSelectedRunId(run.runId)}
                          className="inline-flex items-center gap-2 rounded-md border border-slate-200 bg-white px-3 py-2 text-[12px] font-semibold text-slate-700 transition hover:border-blue-200 hover:bg-blue-50 hover:text-blue-700"
                        >
                          <Eye size={14} />
                          View details
                        </button>
                      </td>
                    </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

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
                  Run #{selectedRun.runId} validation details
                </h3>
                <p className="mt-1 text-[13px] text-slate-500">
                  {selectedRun.findings.length} checks, {selectedRun.failed} failed, {selectedRun.passed} passed
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
                <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">Total checks</p>
                <p className="mt-1 text-[22px] font-semibold text-slate-950">{selectedRun.findings.length}</p>
              </div>
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">Failed</p>
                <p className="mt-1 text-[22px] font-semibold text-red-600">{selectedRun.failed}</p>
              </div>
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500">Passed</p>
                <p className="mt-1 text-[22px] font-semibold text-green-600">{selectedRun.passed}</p>
              </div>
            </div>

            <div className="min-h-0 flex-1 overflow-auto p-6">
              <div className="mb-4 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                <div>
                  <p className="text-[14px] font-semibold text-slate-900">
                    Issue summary
                  </p>
                  <p className="mt-1 text-[13px] leading-5 text-slate-500">
                    Grouped from stored validation findings, with readable cause and next action guidance.
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

              {explanationLoading && (
                <div className="mb-6 rounded-xl border border-slate-200 bg-slate-50 px-5 py-4 text-[13px] text-slate-500">
                  Generating AI explanation from stored data quality findings...
                </div>
              )}

              {!explanationLoading && explanation && (
                <div className="mb-6">
                  <InsightExplanationCard
                    title={explanation.title}
                    summary={explanation.summary}
                    sections={explanation.sections}
                    provider={explanation.provider}
                    model={explanation.model}
                  />
                </div>
              )}

              {selectedIssueGroups.length > 0 ? (
                <div className="mb-6 grid gap-3">
                  {selectedIssueGroups.map((issue) => (
                    <div
                      key={issue.key}
                      className="rounded-lg border border-slate-200 bg-white p-4 shadow-[0_10px_28px_rgba(15,23,42,0.04)]"
                    >
                      <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                        <div className="min-w-0">
                          <div className="flex flex-wrap items-center gap-2">
                            <span
                              className={`inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-[12px] font-semibold capitalize ${getSeverityClass(
                                issue.severity,
                              )}`}
                            >
                              <AlertTriangle size={14} />
                              {issue.severity}
                            </span>
                            <span className="inline-flex items-center gap-1.5 rounded-md border border-slate-200 bg-slate-50 px-2.5 py-1 text-[12px] font-semibold text-slate-600">
                              <ListChecks size={14} />
                              {issue.findings.length} finding{issue.findings.length === 1 ? "" : "s"}
                            </span>
                          </div>
                          <h4 className="mt-3 text-[16px] font-semibold leading-6 text-slate-950">
                            {issue.title}
                          </h4>
                          <p className="mt-1 text-[13px] leading-6 text-slate-600">
                            {issue.columns.length > 0
                              ? `Affected columns: ${issue.columns.join(", ")}`
                              : "Run-level issue"}
                          </p>
                        </div>
                      </div>

                      <div className="mt-4 grid gap-3 lg:grid-cols-2">
                        <div className="rounded-md border border-slate-200 bg-slate-50 p-3">
                          <p className="flex items-center gap-2 text-[12px] font-semibold text-slate-700">
                            <Info size={14} />
                            Likely root cause
                          </p>
                          <p className="mt-2 text-[13px] leading-6 text-slate-600">{issue.cause}</p>
                        </div>
                        <div className="rounded-md border border-blue-100 bg-blue-50 p-3">
                          <p className="text-[12px] font-semibold text-blue-800">Recommended action</p>
                          <p className="mt-2 text-[13px] leading-6 text-blue-900">{issue.action}</p>
                        </div>
                      </div>

                      <div className="mt-4 grid gap-2">
                        {issue.findings.slice(0, 3).map((finding) => (
                          <div
                            key={finding.id}
                            className="rounded-md border border-slate-200 bg-white px-3 py-2 text-[12px] leading-5 text-slate-600"
                          >
                            <span className="font-semibold text-slate-800">
                              {finding.column_name || "Run-level"}:
                            </span>{" "}
                            {getFindingMessage(finding)}
                          </div>
                        ))}
                        {issue.findings.length > 3 && (
                          <p className="text-[12px] text-slate-400">
                            +{issue.findings.length - 3} more finding{issue.findings.length - 3 === 1 ? "" : "s"} in the audit table below
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="mb-6 rounded-lg border border-green-200 bg-green-50 p-4">
                  <p className="text-[14px] font-semibold text-green-800">No failed issue groups</p>
                  <p className="mt-1 text-[13px] leading-5 text-green-700">
                    This run has no failed stored quality checks.
                  </p>
                </div>
              )}

              <div className="mb-4">
                <p className="text-[14px] font-semibold text-slate-900">
                  Validation audit
                </p>
                <p className="mt-1 text-[13px] leading-5 text-slate-500">
                  Individual checks saved for this run, including thresholds and observed values.
                </p>
              </div>

              <div className="overflow-hidden rounded-md border border-slate-200 bg-white">
                <div className="grid gap-4 border-b border-slate-200 bg-slate-50 px-4 py-3 text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-500 lg:grid-cols-[120px_minmax(140px,1fr)_160px_minmax(220px,1.5fr)_170px]">
                  <span>Result</span>
                  <span>Column Scope</span>
                  <span>Check Type</span>
                  <span>Details</span>
                  <span className="text-right">Detected At</span>
                </div>
                {selectedRun.findings.map((finding) => (
                  <div
                    key={finding.id}
                    className="grid gap-4 border-b border-slate-200 px-4 py-3 last:border-b-0 lg:grid-cols-[120px_minmax(140px,1fr)_160px_minmax(220px,1.5fr)_170px]"
                  >
                    <div>
                      {finding.success ? (
                        <span className="inline-flex items-center rounded-md border border-green-200 bg-green-50 px-2.5 py-1 text-[12px] font-semibold text-green-700">
                          <CheckCircle2 size={14} className="mr-1.5" />
                          Passed
                        </span>
                      ) : (
                        <span className="inline-flex items-center rounded-md border border-red-200 bg-red-50 px-2.5 py-1 text-[12px] font-semibold text-red-700">
                          <XCircle size={14} className="mr-1.5" />
                          Failed
                        </span>
                      )}
                    </div>
                    <span className="font-mono text-[12px] text-slate-700">
                      {finding.column_name || "Run-level check"}
                    </span>
                    <span className="text-[12px] font-semibold text-slate-700">
                      {humanizeCheckType(finding.check_type)}
                    </span>
                    <div className="min-w-0 text-[12px] text-slate-500">
                      <DetailRows details={finding.details} />
                    </div>
                    <span className="text-right text-[12px] text-slate-500">
                      {formatDate(finding.created_at)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </aside>
        </div>
      )}
    </div>
  );
}
