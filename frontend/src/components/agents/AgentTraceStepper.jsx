import { useMemo } from "react";
import { CheckCircle2, Loader2, Circle, AlertCircle } from "lucide-react";

export const AGENT_STEP_DEFS = [
  {
    key: "detection",
    label: "Detection",
    description: "Loading drift and data quality findings from the database",
  },
  {
    key: "reasoning",
    label: "AI Reasoning",
    description: "LLM is analyzing the root cause of the failure",
  },
  {
    key: "parser",
    label: "Parsing",
    description: "Structuring the AI response into failure types and severity",
  },
  {
    key: "reporting",
    label: "Reporting",
    description: "Writing the final incident report to the database",
  },
];

export default function AgentTraceStepper({ steps = [], isLive = false }) {
  const statusMap = useMemo(() => resolveStatusMap(steps), [steps]);
  const messageByIndex = useMemo(() => {
    const messages = new Map();

    steps.forEach((step) => {
      if (step?.step_index === undefined || !step?.message) return;
      messages.set(step.step_index, step.message);
    });

    return messages;
  }, [steps]);

  const allDone = AGENT_STEP_DEFS.every(
    (step) => statusMap[step.key] === "done" || statusMap[step.key] === "error",
  );

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-[0_4px_20px_rgba(15,23,42,0.05)]">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <p className="text-[13px] font-semibold text-slate-900">
            AI Agent Execution Trace
          </p>
          <p className="mt-0.5 text-[12px] text-slate-400">
            {isLive
              ? "Live - agents are running..."
              : allDone
                ? "Completed - all 4 nodes executed"
                : "Loaded from stored agent run logs"}
          </p>
        </div>
        {isLive && (
          <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-[11px] font-semibold text-emerald-700">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-500" />
            Live
          </span>
        )}
      </div>

      <ol className="relative flex flex-col gap-0">
        {AGENT_STEP_DEFS.map((stepDef, index) => {
          const status = statusMap[stepDef.key] ?? "pending";
          const isLast = index === AGENT_STEP_DEFS.length - 1;
          const liveMsg = messageByIndex.get(index) || "";

          return (
            <li key={stepDef.key} className="flex gap-4">
              <div className="flex flex-col items-center">
                <StepIcon status={status} />
                {!isLast && (
                  <div
                    className={`my-1 w-px flex-1 transition-colors duration-500 ${
                      status === "done"
                        ? "bg-emerald-300"
                        : status === "running"
                          ? "bg-blue-200"
                          : "bg-slate-200"
                    }`}
                    style={{ minHeight: 20 }}
                  />
                )}
              </div>

              <div className="pb-5">
                <p
                  className={`text-[13px] font-semibold transition-colors ${
                    status === "done"
                      ? "text-emerald-700"
                      : status === "running"
                        ? "text-blue-700"
                        : status === "error"
                          ? "text-red-600"
                          : "text-slate-400"
                  }`}
                >
                  {stepDef.label}
                </p>
                <p className="mt-0.5 text-[12px] leading-5 text-slate-400">
                  {liveMsg || stepDef.description}
                </p>
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}

function StepIcon({ status }) {
  const base =
    "mt-0.5 h-6 w-6 shrink-0 rounded-full flex items-center justify-center";

  if (status === "done") {
    return (
      <div className={`${base} bg-emerald-100 text-emerald-600`}>
        <CheckCircle2 size={14} />
      </div>
    );
  }

  if (status === "running") {
    return (
      <div className={`${base} bg-blue-100 text-blue-600`}>
        <Loader2 size={14} className="animate-spin" />
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className={`${base} bg-red-100 text-red-600`}>
        <AlertCircle size={14} />
      </div>
    );
  }

  return (
    <div className={`${base} bg-slate-100 text-slate-400`}>
      <Circle size={14} />
    </div>
  );
}

function resolveStatusMap(steps) {
  if (!Array.isArray(steps) || steps.length === 0) return {};

  const isLiveFormat = steps.some((step) => step.status !== undefined);

  if (isLiveFormat) {
    const map = {};
    steps.forEach((step) => {
      const def = AGENT_STEP_DEFS[step.step_index];
      if (def) map[def.key] = step.status;
    });
    return map;
  }

  const map = {};
  steps.forEach((log) => {
    const def = AGENT_STEP_DEFS[log.step_index];
    if (!def) return;
    if (!map[def.key]) map[def.key] = "done";
    if (log.log_type === "error") map[def.key] = "error";
  });
  return map;
}
