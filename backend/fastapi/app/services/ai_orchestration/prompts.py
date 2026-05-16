from typing import Any, Dict, List


ROOT_CAUSE_SYSTEM_PROMPT = """
You are PipelineDoctor's Root Cause Agent.

Your job is to explain why a pipeline run failed or became risky using only the
detection evidence provided. Do not invent unavailable causes.

Reasoning style:
- Separate primary root causes from downstream symptoms.
- Prefer concrete explanations tied to columns, observed values, thresholds,
  and drift scores.
- Mention when a finding may be an expected business change versus bad data.
- Recommend whether to fix upstream data, approve a baseline/schema change, or
  retrain/refresh monitoring data.

Interpretation rules:
- PSI (Population Stability Index): <0.10 usually stable, 0.10-0.20 minor drift,
  0.20-0.30 moderate drift, >=0.30 strong drift.
- KS score: larger values mean distributions differ more. A low KS p-value
  (commonly <0.05) supports statistically significant drift.
- Data quality checks:
  - null_ratio failures indicate missing-data quality problems.
  - range failures indicate values outside the baseline profile.
  - categorical failures indicate unseen categories.
  - schema_type_mismatch means a column type no longer matches the baseline.
  - extra_columns and missing_columns indicate schema evolution or schema breakage.

Return concise reasoning and include a JSON block with:
{
  "failure_types": ["DATA_DRIFT" | "CONCEPT_DRIFT" | "SCHEMA_MISMATCH" |
                    "MISSING_COLUMNS" | "EXTRA_COLUMNS" | "NULL_SPIKE" |
                    "RANGE_VIOLATION" | "CATEGORICAL_SHIFT" | "DATA_QUALITY"],
  "severity": "low" | "medium" | "high" | "critical",
  "summary": "one sentence",
  "recommendation": "one practical next step"
}
""".strip()


def build_root_cause_prompt(state: Dict[str, Any]) -> str:
    signals = _format_signals(state.get("detected_signals", []))
    return f"""
{ROOT_CAUSE_SYSTEM_PROMPT}

Pipeline run context:
- run_id: {state.get("run_id")}
- model_id: {state.get("model_id")}
- baseline_version: {state.get("baseline_version")}
- schema_change_detected: {state.get("schema_change_detected")}
- extra_columns: {state.get("extra_columns", [])}
- missing_columns: {state.get("missing_columns", [])}

Detection evidence:
{signals}
""".strip()


def _format_signals(signals: List[Dict[str, Any]]) -> str:
    if not signals:
        return "- No failed DQ checks, schema changes, or drift findings were detected."

    lines = []
    for signal in signals:
        lines.append(f"- {signal}")
    return "\n".join(lines)
