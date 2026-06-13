import { useMemo } from "react";
import { CheckCircle2, Loader2, Circle, AlertCircle } from "lucide-react";

const AGENT_STEP_DEFS = [
  {
    key: "detection",
    label: "Detection",
    description: "Loading drift and data quality findings from the database",
    runningDescription: "System is detecting drift, schema, and data quality signals.",
    pendingDescription: "Waiting to start evidence detection.",
  },
  {
    key: "reasoning",
    label: "AI Reasoning",
    description: "LLM is analyzing the root cause of the failure",
    runningDescription: "System is reasoning over the detected failure signals.",
    pendingDescription: "Waiting for evidence detection to finish.",
  },
  {
    key: "parser",
    label: "Parsing",
    description: "Structuring the AI response into failure types and severity",
    runningDescription: "System is parsing the AI response into structured RCA fields.",
    pendingDescription: "Waiting for AI reasoning to finish.",
  },
  {
    key: "reporting",
    label: "Reporting",
    description: "Writing the final incident report to the database",
    runningDescription: "System is finalizing and saving the RCA report.",
    pendingDescription: "Waiting for parsing to finish before saving the report.",
  },
];

export default function AgentTraceStepper({ steps = [], isLive = false }) {
  const statusMap = useMemo(() => resolveStatusMap(steps, isLive), [steps, isLive]);
  const messageByIndex = useMemo(() => {
    const messages = new Map();

    steps.forEach((step) => {
      if (step?.step_index === undefined || !step?.message) return;
      messages.set(Number(step.step_index), step.message);
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
          const bodyCopy = resolveStepCopy(stepDef, status, liveMsg);

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
                  {bodyCopy}
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

function resolveStatusMap(steps, isLive) {
  if (!Array.isArray(steps) || steps.length === 0) return {};

  if (isLive) {
    const map = {};
    steps.forEach((step) => {
      const stepIndex = Number(step.step_index);
      const def = AGENT_STEP_DEFS[stepIndex];
      if (!def) return;

      map[def.key] = step.status || "pending";
    });
    return map;
  }

  const map = {};
  steps.forEach((log) => {
    const stepIndex = Number(log.step_index);
    const def = AGENT_STEP_DEFS[stepIndex];
    if (!def) return;
    if (!map[def.key]) map[def.key] = "done";
    if (log.log_type === "error") map[def.key] = "error";
  });
  return map;
}

function resolveStepCopy(stepDef, status, liveMsg) {
  if (liveMsg) return liveMsg;
  if (status === "running") return stepDef.runningDescription || stepDef.description;
  if (status === "pending") return stepDef.pendingDescription || stepDef.description;
  return stepDef.description;
}
