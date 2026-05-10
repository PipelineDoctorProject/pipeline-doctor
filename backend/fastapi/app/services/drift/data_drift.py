import numpy as np
import pandas as pd
from evidently import Report
from evidently.presets import DataDriftPreset
from app.services.drift.metrics import calculate_psi, calculate_ks
from app.services.drift.utils import classify_drift_severity

def check_data_drift(reference_data: pd.DataFrame, current_data: pd.DataFrame):
    results = []
    
    numeric_cols = current_data.select_dtypes(include=[np.number]).columns.tolist()
    feature_names = [col for col in numeric_cols if col in reference_data.columns]

    if not feature_names:
        print("No matching numeric features found for data drift detection.")
        return results, feature_names

    try:
        report = Report([DataDriftPreset()])
        report.run(
            current_data=current_data[feature_names],
            reference_data=reference_data[feature_names]
        )
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
