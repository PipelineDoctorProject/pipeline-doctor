import numpy as np
import pandas as pd
from evidently import Report
from evidently.presets import DataDriftPreset
from app.services.drift.metrics import calculate_psi, calculate_ks
from app.services.drift.utils import classify_drift_severity
from app.config import settings
from evidently.ui.workspace import Workspace

IDENTIFIER_TOKENS = {"id", "uuid", "key"}


def _is_identifier_column(col: str) -> bool:
    normalized = col.strip().lower().replace("_", "")
    return normalized in IDENTIFIER_TOKENS or normalized.endswith("id")

def check_data_drift(reference_data: pd.DataFrame, current_data: pd.DataFrame):
    results = []

    shared_cols = [col for col in current_data.columns if col in reference_data.columns]
    numeric_cols = []
    for col in shared_cols:
        reference_numeric = pd.to_numeric(reference_data[col], errors="coerce")
        current_numeric = pd.to_numeric(current_data[col], errors="coerce")

        if reference_numeric.notna().sum() > 0 and current_numeric.notna().sum() > 0:
            reference_data[col] = reference_numeric
            current_data[col] = current_numeric
            numeric_cols.append(col)

    feature_names = [
        col
        for col in numeric_cols
        if col in reference_data.columns and not _is_identifier_column(col)
    ]

    if not feature_names:
        print("No matching numeric features found for data drift detection.")
        return results, feature_names

    try:
        report = Report([DataDriftPreset()])
        # Run the report and CAPTURE the resulting Snapshot object
        snapshot = report.run(
            current_data=current_data[feature_names],
            reference_data=reference_data[feature_names]
        )
        
        # --- EVIDENTLY CLOUD INTEGRATION (Verified for 0.7.21) ---
        if settings.EVIDENTLY_TOKEN:
            try:
                from evidently.ui.workspace import CloudWorkspace
                ws = CloudWorkspace(
                    token=settings.EVIDENTLY_TOKEN,
                    url="https://app.evidently.cloud"
                )
                
                # Auto-discover project by name from settings
                project = None
                projects = ws.list_projects()
                target_name = settings.EVIDENTLY_PROJECT_NAME
                
                for p in projects:
                    if p.name == target_name or p.name.lower() == target_name.lower():
                        project = p
                        break
                
                if project:
                    # Use the snapshot object we captured from run()
                    ws.add_run(project.id, snapshot)
                    print(f"Successfully pushed drift snapshot to Project: {project.name}")
                else:
                    print(f"Project not found. Available projects: {[p.name for p in projects]}")
                    
            except Exception as cloud_err:
                print(f"Failed to push to Evidently Cloud: {cloud_err}")
                
    except Exception as e:
        print(f"Evidently AI report generation failed: {e}")

    for feature_name in feature_names:
        reference_values = reference_data[feature_name].values
        current_values = current_data[feature_name].values

        psi_score = calculate_psi(reference_values, current_values)
        ks_score, ks_pvalue = calculate_ks(reference_values, current_values)
        drift_score = max(psi_score, ks_score)
        severity = classify_drift_severity(drift_score)

        results.append({
            "feature_name": feature_name,
            "psi_score": psi_score,
            "ks_score": ks_score,
            "ks_pvalue": ks_pvalue,
            "drift_score": drift_score,
            "severity": severity,
            "type": "data_drift"
        })
        
    return results, feature_names


def check_profile_drift(current_data: pd.DataFrame, baseline_profile: dict):
    results = []
    feature_names = []

    for feature_name, rules in (baseline_profile or {}).items():
        if str(feature_name).startswith("_") or not isinstance(rules, dict):
            continue

        if _is_identifier_column(str(feature_name)) or feature_name not in current_data.columns:
            continue

        if rules.get("type") == "numeric" or {"min", "max"}.issubset(rules.keys()):
            series = pd.to_numeric(current_data[feature_name], errors="coerce").dropna()
            if series.empty:
                continue

            baseline_min = float(rules.get("min", series.min()))
            baseline_max = float(rules.get("max", series.max()))
            baseline_mean = rules.get("mean")
            baseline_range = max(baseline_max - baseline_min, 1.0)

            observed_min = float(series.min())
            observed_max = float(series.max())
            observed_mean = float(series.mean())

            below_ratio = float((series < baseline_min).mean())
            above_ratio = float((series > baseline_max).mean())
            range_expansion = max(
                0.0,
                baseline_min - observed_min,
                observed_max - baseline_max,
            ) / baseline_range

            mean_shift = 0.0
            if baseline_mean is not None:
                mean_shift = abs(observed_mean - float(baseline_mean)) / baseline_range

            drift_score = max(below_ratio + above_ratio, range_expansion, mean_shift)
            severity = classify_drift_severity(drift_score)
            feature_names.append(feature_name)
            results.append({
                "feature_name": feature_name,
                "psi_score": drift_score,
                "ks_score": 0.0,
                "ks_pvalue": 1.0,
                "drift_score": drift_score,
                "severity": severity,
                "type": "data_drift",
            })
            continue

        if "unique_values" in rules:
            allowed = {str(value).strip().upper() for value in rules.get("unique_values") or []}
            if not allowed:
                continue

            observed = current_data[feature_name].dropna().astype(str).str.strip().str.upper()
            if observed.empty:
                continue

            unseen_ratio = float((~observed.isin(allowed)).mean())
            severity = classify_drift_severity(unseen_ratio)
            feature_names.append(feature_name)
            results.append({
                "feature_name": feature_name,
                "psi_score": unseen_ratio,
                "ks_score": 0.0,
                "ks_pvalue": 1.0,
                "drift_score": unseen_ratio,
                "severity": severity,
                "type": "data_drift",
            })

    return results, feature_names
