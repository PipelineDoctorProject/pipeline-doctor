# AI Orchestration (LangGraph RCA)

This document explains the AI root cause analysis system added this week.

The goal of the orchestration layer is to convert failed monitoring evidence into a structured RCA report that users can read directly in the incident drawer.

---

## What It Does

For a monitored pipeline run, the AI layer:

1. loads drift, schema, and data quality evidence
2. asks the RCA model to reason about the likely cause
3. parses the response into a structured report
4. marks the report ready for the frontend

---

## Core Files

| File | Responsibility |
|---|---|
| `backend/fastapi/app/services/ai_orchestration/supervisor.py` | Main RCA graph and step definitions |
| `backend/fastapi/app/services/ai/context_builder.py` | Builds run-specific monitoring context |
| `backend/fastapi/app/tasks/ai_tasks.py` | Celery task that executes the doctor agent |
| `backend/fastapi/app/services/ai_orchestration/prompts.py` | RCA prompt builder |
| `backend/fastapi/app/services/ai_orchestration/parser.py` | Structured output parsing |
| `backend/fastapi/app/services/ai_orchestration/llm_client.py` | LLM provider integration |

---

## 4-Step RCA Flow

The orchestration uses these four steps:

1. `Detection`
2. `AI Reasoning`
3. `Parsing`
4. `Reporting`

### Detection

The system loads:

- data quality findings
- drift findings
- schema changes

These are normalized into `detected_signals`.

### AI Reasoning

The system builds a root-cause prompt and sends it to the configured LLM.

If no live LLM is available, the system falls back to deterministic rule-based reasoning.

### Parsing

The system extracts:

- `failure_types`
- `severity`
- `summary`
- `recommendation`

The parser also guards against under-reporting by comparing parsed severity with detected signal severity and keeping the worse one.

### Reporting

The system creates the final RCA payload that is attached to the incident and later shown in the frontend.

---

## Graph Design

**File:** `backend/fastapi/app/services/ai_orchestration/supervisor.py`

When LangGraph is installed, the RCA flow is built as a graph:

```text
detection -> reasoning -> parser -> reporting -> END
```

If LangGraph is unavailable, the project falls back to a sequential supervisor with the same step order. That keeps RCA available even in simpler environments.

---

## Agent State

The supervisor moves a shared state object across the nodes. It carries:

- run metadata
- model id
- baseline version
- schema change information
- data quality findings
- drift findings
- detected signals
- root-cause prompt
- model reasoning output
- parsed report fields
- final RCA report

This shared state is what makes the graph deterministic and debuggable.

---

## Output Shape

The reporting step creates a payload like:

```json
{
  "title": "AI Root Cause Analysis",
  "run_id": 10,
  "failure_types": ["RANGE_VIOLATION", "EXTRA_COLUMNS"],
  "severity": "medium",
  "summary": "Pipeline run failed because values moved outside the baseline range and an extra column was present.",
  "recommendation": "Inspect bad rows first and update the baseline only if the upstream change is expected.",
  "issues": [],
  "evidence": []
}
```

This is the report consumed by the incident drawer.

---

## Fallback Behavior

The orchestration is resilient by design:

- no LangGraph -> sequential supervisor
- no LLM -> deterministic RCA fallback
- Redis live publish failure -> main RCA task still completes

That means the RCA system degrades gracefully instead of failing completely.

---

## UI Behavior

The incident drawer now follows the real RCA lifecycle:

1. show the live execution trace
2. show dynamic step messages while the agent is running
3. reveal the final RCA report only after the `Reporting` step finishes

This prevents users from seeing a premature RCA card before persistence is complete.

---

## Related Docs

- [realtime_tracing.md](./realtime_tracing.md)
- [automation_and_scheduler.md](./automation_and_scheduler.md)
