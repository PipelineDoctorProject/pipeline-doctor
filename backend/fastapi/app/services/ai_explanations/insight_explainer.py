import json
from typing import Any

from app.models.data_quality import DataQualityFinding
from app.models.drift_finding import DriftFinding
from app.services.ai_orchestration.llm_client import (
    get_configured_model_name,
    get_default_llm_callable,
)


def build_data_quality_explanation(
    run_id: int,
    findings: list[DataQualityFinding],
) -> dict[str, Any]:
    failed_findings = [finding for finding in findings if not finding.success]

    if not failed_findings:
        return {
            "title": "AI Explanation",
            "summary": "This run did not store any failed data quality checks.",
            "sections": [
                {
                    "label": "Why This Matters",
                    "content": "The current batch passed the stored validation checks, so there is no quality risk that needs explanation for this run.",
                },
                {
                    "label": "Suggested Remediation",
                    "content": "No action is required. Keep monitoring future runs and only investigate if new failed checks appear.",
                },
            ],
            "provider": "fallback",
            "model": "deterministic-rules",
        }

    llm = get_default_llm_callable()
    if llm:
        try:
            prompt = _build_data_quality_prompt(run_id, failed_findings)
            parsed = _extract_json_payload(llm(prompt))
            return {
                "title": "AI Explanation",
                "summary": parsed.get("summary") or _fallback_data_quality_summary(failed_findings),
                "sections": [
                    {
                        "label": "Why This Matters",
                        "content": parsed.get("why_this_matters") or _fallback_data_quality_why(failed_findings),
                    },
                    {
                        "label": "Suggested Remediation",
                        "content": parsed.get("suggested_remediation") or _fallback_data_quality_action(failed_findings),
                    },
                ],
                "provider": "groq",
                "model": get_configured_model_name() or "llm",
            }
        except Exception:
            pass

    return {
        "title": "AI Explanation",
        "summary": _fallback_data_quality_summary(failed_findings),
        "sections": [
            {
                "label": "Why This Matters",
                "content": _fallback_data_quality_why(failed_findings),
            },
            {
                "label": "Suggested Remediation",
                "content": _fallback_data_quality_action(failed_findings),
            },
        ],
        "provider": "fallback",
        "model": "deterministic-rules",
    }


def build_drift_explanation(
    run_id: int,
    findings: list[DriftFinding],
) -> dict[str, Any]:
    drifted_findings = [finding for finding in findings if finding.drift_detected]

    if not drifted_findings:
        return {
            "title": "AI Explanation",
            "summary": "This run did not store any active drift signals.",
            "sections": [
                {
                    "label": "Possible Business Interpretation",
                    "content": "The monitored feature distributions are currently close to the baseline, so this run does not show a meaningful population shift.",
                },
                {
                    "label": "What Changed Compared To Baseline",
                    "content": "No material distribution change was stored for this run. Continue monitoring future runs for emerging drift trends.",
                },
            ],
            "provider": "fallback",
            "model": "deterministic-rules",
        }

    llm = get_default_llm_callable()
    if llm:
        try:
            prompt = _build_drift_prompt(run_id, drifted_findings)
            parsed = _extract_json_payload(llm(prompt))
            return {
                "title": "AI Explanation",
                "summary": parsed.get("summary") or _fallback_drift_summary(drifted_findings),
                "sections": [
                    {
                        "label": "Possible Business Interpretation",
                        "content": parsed.get("business_interpretation") or _fallback_drift_interpretation(drifted_findings),
                    },
                    {
                        "label": "What Changed Compared To Baseline",
                        "content": parsed.get("what_changed_compared_to_baseline") or _fallback_drift_change(drifted_findings),
                    },
                ],
                "provider": "groq",
                "model": get_configured_model_name() or "llm",
            }
        except Exception:
            pass

    return {
        "title": "AI Explanation",
        "summary": _fallback_drift_summary(drifted_findings),
        "sections": [
            {
                "label": "Possible Business Interpretation",
                "content": _fallback_drift_interpretation(drifted_findings),
            },
            {
                "label": "What Changed Compared To Baseline",
                "content": _fallback_drift_change(drifted_findings),
            },
        ],
        "provider": "fallback",
        "model": "deterministic-rules",
    }


def _build_data_quality_prompt(run_id: int, findings: list[DataQualityFinding]) -> str:
    serialized = [
        {
            "column": finding.column_name,
            "check_type": finding.check_type,
            "details": finding.details,
        }
        for finding in findings
    ]
    return (
        "You are explaining stored data quality failures for an ML monitoring platform.\n"
        "Do not decide whether a check failed; that is already determined.\n"
        "Summarize the user impact and likely remediation in plain product language.\n"
        "Return only JSON with keys: summary, why_this_matters, suggested_remediation.\n"
        f"Run ID: {run_id}\n"
        f"Failed findings: {json.dumps(serialized, default=str)}"
    )


def _build_drift_prompt(run_id: int, findings: list[DriftFinding]) -> str:
    serialized = [
        {
            "feature_name": finding.feature_name,
            "drift_score": finding.drift_score,
            "psi_score": finding.psi_score,
            "ks_score": finding.ks_score,
            "ks_pvalue": finding.ks_pvalue,
            "severity": finding.severity,
        }
        for finding in findings
    ]
    return (
        "You are explaining stored drift findings for an ML monitoring platform.\n"
        "Do not decide whether drift exists; that is already determined.\n"
        "Interpret the business meaning of the stored drift signals and describe how the current batch differs from baseline.\n"
        "Return only JSON with keys: summary, business_interpretation, what_changed_compared_to_baseline.\n"
        f"Run ID: {run_id}\n"
        f"Drift findings: {json.dumps(serialized, default=str)}"
    )


def _extract_json_payload(text: str) -> dict[str, Any]:
    if not text:
        raise ValueError("Empty explanation payload")

    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in explanation payload")

    return json.loads(text[start : end + 1])


def _fallback_data_quality_summary(findings: list[DataQualityFinding]) -> str:
    check_types = sorted({finding.check_type for finding in findings if finding.check_type})
    columns = sorted({finding.column_name for finding in findings if finding.column_name})
    scope = ", ".join(columns[:4]) if columns else "the incoming dataset"
    checks = ", ".join(check_types[:3]) if check_types else "data quality"
    return (
        f"Run #{findings[0].pipeline_run_id} failed stored {checks} checks affecting {scope}."
    )


def _fallback_data_quality_why(findings: list[DataQualityFinding]) -> str:
    check_types = {finding.check_type for finding in findings}
    if "missing_columns" in check_types or "schema_type_mismatch" in check_types:
        return (
            "These failures can break feature compatibility with the active model or downstream pipeline, so predictions may become unreliable even if the upload technically succeeds."
        )
    if "range" in check_types or "categorical" in check_types:
        return (
            "These failures suggest the current batch no longer matches the baseline profile, which can degrade model behavior or hide upstream source changes."
        )
    return (
        "These failed checks indicate that the incoming batch differs from the validated baseline contract and should be reviewed before treating the run as trustworthy."
    )


def _fallback_data_quality_action(findings: list[DataQualityFinding]) -> str:
    columns = sorted({finding.column_name for finding in findings if finding.column_name})
    if columns:
        return (
            f"Review the affected columns first ({', '.join(columns[:5])}), inspect a few failing rows, and decide whether the source data is malformed or the baseline needs to be refreshed."
        )
    return (
        "Inspect the failing run-level checks, compare the incoming file with the active baseline, and only update the baseline if the upstream change is expected."
    )


def _fallback_drift_summary(findings: list[DriftFinding]) -> str:
    features = sorted({finding.feature_name for finding in findings if finding.feature_name})
    scope = ", ".join(features[:4]) if features else "multiple features"
    return f"Run #{findings[0].run_id} stored active drift signals for {scope}."


def _fallback_drift_interpretation(findings: list[DriftFinding]) -> str:
    severe = [finding for finding in findings if str(finding.severity).lower() in {"high", "critical"}]
    if severe:
        return (
            "The batch appears to come from a meaningfully different population than the baseline, which can happen after source changes, seasonality, traffic mix changes, or stale reference data."
        )
    return (
        "The batch shows measurable distribution change versus baseline, but the signal should still be interpreted alongside source context and recent business changes."
    )


def _fallback_drift_change(findings: list[DriftFinding]) -> str:
    strongest = sorted(findings, key=lambda finding: float(finding.drift_score or 0), reverse=True)[:3]
    parts = []
    for finding in strongest:
        parts.append(
            f"{finding.feature_name} (score {float(finding.drift_score or 0):.3f}, PSI {float(finding.psi_score or 0):.3f})"
        )
    if parts:
        return (
            "Compared with the baseline, the strongest movement was observed in "
            + ", ".join(parts)
            + ". Review whether the batch source, population, or time window changed."
        )
    return (
        "Compared with the baseline, one or more monitored feature distributions shifted enough to trigger drift storage for this run."
    )
