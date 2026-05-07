#drift_service.py
import numpy as np
import pandas as pd

from evidently import Report
from evidently.presets import DataDriftPreset
from sqlalchemy.orm import Session

from app.models.drift_finding import DriftFinding
from app.models.pipeline_run import PipelineRun
from app.services.drift.metrics import (
    calculate_psi,
    calculate_ks
)


def classify_drift_severity(drift_score: float) -> str:
    if drift_score >= 0.5:
        return "critical"

    if drift_score >= 0.3:
        return "high"

    if drift_score >= 0.2:
        return "medium"

    return "low"


def run_drift_checks(db: Session, run: PipelineRun, X):
    feature_names = ["feature_1", "feature_2", "feature_3"]

    reference_data = pd.DataFrame(
        np.random.normal(0.5, 0.1, (1000, 3)),
        columns=feature_names
    )

    current_data = pd.DataFrame(
        np.nan_to_num(X, nan=0.0),
        columns=feature_names
    )

    report = Report([DataDriftPreset()])

    report.run(
        current_data=current_data,
        reference_data=reference_data
    )

    for feature_name in feature_names:
        reference_values = reference_data[feature_name].values
        current_values = current_data[feature_name].values

        psi_score = calculate_psi(
            reference_values,
            current_values
        )

        ks_score, ks_pvalue = calculate_ks(
            reference_values,
            current_values
        )

        drift_score = max(psi_score, ks_score)

        drift_detected = (
            psi_score > 0.2 or
            ks_score > 0.2 or
            ks_pvalue < 0.05
        )

        severity = classify_drift_severity(drift_score)

        db.add(DriftFinding(
            run_id=run.id,
            feature_name=feature_name,

            psi_score=psi_score,
            ks_score=ks_score,
            ks_pvalue=ks_pvalue,

            drift_score=drift_score,
            drift_detected=drift_detected,
            severity=severity
        ))