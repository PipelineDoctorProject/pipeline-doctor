import { Brain, AlertTriangle, Lightbulb, Wrench, ChevronDown, ChevronUp, BadgeCheck } from "lucide-react";
import { useState } from "react";

const SEVERITY_STYLES = {
  critical: "border-red-200 bg-red-50 text-red-700",
  high: "border-orange-200 bg-orange-50 text-orange-700",
  medium: "border-amber-200 bg-amber-50 text-amber-700",
  low: "border-blue-200 bg-blue-50 text-blue-700",
};

function SeverityBadge({ severity }) {
  const s = String(severity || "low").toLowerCase();
  const cls = SEVERITY_STYLES[s] || SEVERITY_STYLES.low;
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-[11px] font-bold uppercase tracking-wide ${cls}`}
    >
      <AlertTriangle size={11} />
      {s}
    </span>
  );
}

// ---------- Main component ----------
// Props:
//   rcaReport  — the rca_report object from the incident (may be null)
//   guidance   — the guidance object from the incident
//   agentRuns  — array of AgentRun objects fetched from GET /incidents/{id}/agent-runs
export default function IncidentReasoningCard({ rcaReport, guidance, agentRuns = [] }) {
  const [expanded, setExpanded] = useState(false);
  const latestRun = agentRuns[0] ?? null;

  // Nothing to show
  if (!rcaReport && !guidance?.cause) return null;

  const summary = rcaReport?.summary || guidance?.cause || "No summary available.";
  const recommendation = rcaReport?.recommendation || guidance?.action || "Review the evidence.";
  const severity = rcaReport?.severity || "low";
  const provider = rcaReport?.provider || guidance?.source || "fallback";
  const model = rcaReport?.model || guidance?.model || "deterministic-rules";
  const failureTypes = Array.isArray(rcaReport?.failure_types) ? rcaReport.failure_types : [];
  const issues = Array.isArray(rcaReport?.issues) ? rcaReport.issues : [];

  const isLLMPowered = provider !== "fallback" && provider !== "deterministic" && provider !== "metric_interpreter";

  return (
    <div className="overflow-hidden rounded-xl border border-violet-200 bg-white shadow-[0_4px_20px_rgba(109,40,217,0.07)]">
      {/* ── Header ── */}
      <div className="flex items-start justify-between gap-4 border-b border-violet-100 bg-gradient-to-r from-violet-50 to-white px-5 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-violet-100 text-violet-600">
            <Brain size={18} />
          </div>
          <div>
            <p className="text-[13px] font-semibold text-slate-900">
              AI Root Cause Report
            </p>
            <p className="mt-0.5 font-mono text-[11px] text-slate-400">
              {provider} / {model}
            </p>
          </div>
        </div>

        <div className="flex shrink-0 items-center gap-2">
          {isLLMPowered && (
            <span className="inline-flex items-center gap-1 rounded-full border border-violet-200 bg-violet-50 px-2.5 py-0.5 text-[11px] font-semibold text-violet-700">
              <BadgeCheck size={11} />
              LLM-powered
            </span>
          )}
          <SeverityBadge severity={severity} />
        </div>
      </div>

      {/* ── Body ── */}
      <div className="grid gap-4 px-5 py-4 md:grid-cols-2">
        {/* Summary */}
        <div className="flex flex-col gap-1">
          <p className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-slate-500">
            <Lightbulb size={12} />
            Root Cause Summary
          </p>
          <p className="text-[13px] leading-6 text-slate-700">{summary}</p>

          {/* Failure type pills */}
          {failureTypes.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {failureTypes.map((type) => (
                <span
                  key={type}
                  className="rounded-md border border-slate-200 bg-slate-50 px-2 py-0.5 font-mono text-[11px] font-semibold text-slate-600"
                >
                  {type}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Recommendation */}
        <div className="flex flex-col gap-1">
          <p className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-blue-600">
            <Wrench size={12} />
            Recommended Action
          </p>
          <p className="text-[13px] leading-6 text-blue-900">{recommendation}</p>

          {latestRun && (
            <p className="mt-2 text-[11px] text-slate-400">
              Agent run #{latestRun.id} ·{" "}
              {latestRun.status === "completed" ? "✅ Completed" : `Status: ${latestRun.status}`}
            </p>
          )}
        </div>
      </div>

      {/* ── Expandable Evidence Issues ── */}
      {issues.length > 0 && (
        <div className="border-t border-slate-100">
          <button
            onClick={() => setExpanded((prev) => !prev)}
            className="flex w-full items-center justify-between px-5 py-3 text-[12px] font-semibold text-slate-600 transition hover:bg-slate-50"
          >
            <span>Evidence Issues ({issues.length})</span>
            {expanded ? <ChevronUp size={15} /> : <ChevronDown size={15} />}
          </button>

          {expanded && (
            <div className="grid gap-3 px-5 pb-5 pt-1 md:grid-cols-2">
              {issues.map((issue, i) => (
                <div
                  key={`${issue.type}-${i}`}
                  className="rounded-lg border border-slate-200 bg-slate-50 p-3"
                >
                  <div className="mb-1 flex items-center justify-between gap-2">
                    <p className="text-[12px] font-semibold text-slate-900">
                      {issue.title || issue.type}
                    </p>
                    <SeverityBadge severity={issue.severity} />
                  </div>
                  <p className="text-[12px] leading-5 text-slate-600">
                    {issue.likely_root_cause || issue.summary}
                  </p>
                  {issue.recommended_action && (
                    <p className="mt-2 text-[12px] font-medium leading-5 text-blue-700">
                      → {issue.recommended_action}
                    </p>
                  )}
                  {Array.isArray(issue.affected_columns) && issue.affected_columns.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {issue.affected_columns.map((col) => (
                        <span
                          key={col}
                          className="rounded border border-slate-200 bg-white px-1.5 py-0.5 font-mono text-[10px] text-slate-500"
                        >
                          {col}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
