import {
  AlertTriangle,
  Brain,
  FileText,
  Lightbulb,
  Wrench,
} from "lucide-react";
import { Link } from "react-router-dom";

const SEVERITY_STYLES = {
  critical: "border-red-200 bg-red-50 text-red-700",
  high: "border-orange-200 bg-orange-50 text-orange-700",
  medium: "border-amber-200 bg-amber-50 text-amber-700",
  low: "border-blue-200 bg-blue-50 text-blue-700",
};

function SeverityBadge({ severity }) {
  const normalized = String(severity || "low").toLowerCase();
  const className = SEVERITY_STYLES[normalized] || SEVERITY_STYLES.low;

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-md border px-2.5 py-1 text-[11px] font-bold uppercase tracking-wide ${className}`}
    >
      <AlertTriangle size={11} />
      {normalized}
    </span>
  );
}

function getReasoningSource(provider, model) {
  if (provider === "fallback" || model === "deterministic-rules") {
    return {
      label: "Rule-based RCA",
      detail: "Generated from stored drift, schema, and data quality signals.",
    };
  }

  if (provider === "metric_interpreter" || provider === "deterministic") {
    return {
      label: "Structured RCA",
      detail: model ? `${provider} / ${model}` : provider,
    };
  }

  return {
    label: "LLM RCA",
    detail: model ? `${provider} / ${model}` : provider,
  };
}

function OverviewBlock({ icon: Icon, title, tone, children }) {
  const toneClass =
    tone === "blue"
      ? "border-blue-100 bg-blue-50/60"
      : tone === "violet"
        ? "border-violet-100 bg-violet-50/60"
        : "border-slate-200 bg-slate-50";

  const iconClass =
    tone === "blue"
      ? "bg-blue-100 text-blue-700"
      : tone === "violet"
        ? "bg-violet-100 text-violet-700"
        : "bg-slate-200 text-slate-700";

  return (
    <div className={`rounded-lg border p-4 ${toneClass}`}>
      <div className="flex items-center gap-2">
        <div className={`flex h-7 w-7 items-center justify-center rounded-md ${iconClass}`}>
          <Icon size={14} />
        </div>
        <p className="text-[12px] font-semibold uppercase tracking-wide text-slate-700">
          {title}
        </p>
      </div>
      <div className="mt-3 text-[13px] leading-6 text-slate-700">{children}</div>
    </div>
  );
}

export default function IncidentReasoningCard({ rcaReport, guidance, agentRuns = [], incidentId }) {
  const latestRun = agentRuns[0] ?? null;

  if (!rcaReport && !guidance?.cause) return null;

  const reportTitle = rcaReport?.title || "AI Root Cause Report";
  const summary = rcaReport?.summary || guidance?.cause || "No summary available.";
  const recommendation =
    rcaReport?.recommendation || guidance?.action || "Review the evidence.";
  const severity = rcaReport?.severity || "low";
  const provider = rcaReport?.provider || guidance?.source || "fallback";
  const model = rcaReport?.model || guidance?.model || "deterministic-rules";
  const source = getReasoningSource(provider, model);

  return (
    <div className="overflow-hidden rounded-xl border border-violet-200 bg-white shadow-[0_4px_20px_rgba(109,40,217,0.07)]">
      <div className="flex items-start justify-between gap-4 border-b border-violet-100 bg-gradient-to-r from-violet-50 to-white px-5 py-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-violet-100 text-violet-600">
            <Brain size={18} />
          </div>
          <div>
            <p className="text-[13px] font-semibold text-slate-900">{reportTitle}</p>
            <p className="mt-0.5 text-[11px] font-medium text-slate-500">{source.label}</p>
            <p className="mt-0.5 font-mono text-[11px] text-slate-400">{source.detail}</p>
          </div>
        </div>

        <div className="flex shrink-0 items-center gap-2">
          {incidentId && (
            <Link
              to={`/reports/incidents/${incidentId}`}
              className="inline-flex items-center gap-1.5 rounded-md border border-violet-200 bg-white px-2.5 py-1 text-[11px] font-bold uppercase tracking-wide text-violet-700 hover:bg-violet-50"
            >
              <FileText size={12} />
              Full report
            </Link>
          )}
          <SeverityBadge severity={severity} />
        </div>
      </div>

      <div className="grid gap-4 px-5 py-4 md:grid-cols-2">
        <OverviewBlock icon={Lightbulb} title="What Happened" tone="violet">
          {summary}
        </OverviewBlock>

        <OverviewBlock icon={Wrench} title="What To Do Next" tone="blue">
          {recommendation}
          {latestRun && (
            <p className="mt-3 text-[11px] text-slate-500">
              Agent run #{latestRun.id} -{" "}
              {latestRun.status === "completed"
                ? "Completed"
                : `Status: ${latestRun.status}`}
            </p>
          )}
        </OverviewBlock>
      </div>
    </div>
  );
}
