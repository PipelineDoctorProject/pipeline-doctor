import { Brain, Sparkles } from "lucide-react";

function getSourceLabel(provider, model) {
  if (provider === "fallback" || model === "deterministic-rules") {
    return {
      label: "Structured explanation",
      detail: "Generated from stored monitoring signals without a live LLM call.",
    };
  }

  return {
    label: "AI explanation",
    detail: model ? `${provider} / ${model}` : provider,
  };
}

export default function InsightExplanationCard({
  title = "AI Explanation",
  summary,
  sections = [],
  provider = "fallback",
  model = "deterministic-rules",
}) {
  const source = getSourceLabel(provider, model);

  return (
    <div className="rounded-xl border border-violet-200 bg-white shadow-[0_10px_28px_rgba(76,29,149,0.08)]">
      <div className="border-b border-violet-100 bg-gradient-to-r from-violet-50 to-white px-5 py-4">
        <div className="flex items-start gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-violet-100 text-violet-700">
            <Brain size={18} />
          </div>
          <div className="min-w-0">
            <p className="text-[13px] font-semibold text-slate-900">{title}</p>
            <p className="mt-0.5 text-[11px] font-medium text-slate-500">{source.label}</p>
            <p className="mt-0.5 font-mono text-[11px] text-slate-400">{source.detail}</p>
          </div>
        </div>
      </div>

      <div className="px-5 py-4">
        {summary && (
          <div className="mb-4 rounded-lg border border-slate-200 bg-slate-50 p-4">
            <div className="flex items-center gap-2 text-[12px] font-semibold uppercase tracking-wide text-slate-700">
              <Sparkles size={14} />
              Overview
            </div>
            <p className="mt-2 text-[13px] leading-6 text-slate-700">{summary}</p>
          </div>
        )}

        <div className="grid gap-3 md:grid-cols-2">
          {sections.map((section) => (
            <div
              key={section.label}
              className="rounded-lg border border-slate-200 bg-slate-50 p-4"
            >
              <p className="text-[12px] font-semibold uppercase tracking-wide text-slate-700">
                {section.label}
              </p>
              <p className="mt-2 text-[13px] leading-6 text-slate-700">
                {section.content}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
