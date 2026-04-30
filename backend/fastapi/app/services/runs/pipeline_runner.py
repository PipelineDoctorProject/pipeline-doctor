from datetime import datetime
from sqlalchemy.orm import Session
import numpy as np

from app.models.pipeline_run import PipelineRun
from app.models.prediction_log import PredictionLog
from app.models.drift_finding import DriftFinding
from app.models.data_quality import DataQualityFinding
from app.models.incident import Incident
# from app.models.ml_model import MLModel

import mlflow.pyfunc

MODEL_URI = "models:/PipelineDoctorDemoModel/1"
model = mlflow.pyfunc.load_model(MODEL_URI)

# -------------------------------
# DATA GENERATION
# -------------------------------
def generate_data(mode: str = "bad"):
    if mode == "normal":
        return np.random.normal(0.5, 0.1, (100, 3))

    elif mode == "drift":
        return np.random.normal(0.9, 0.1, (100, 3))

    elif mode == "bad":
        X = np.random.normal(0.5, 0.1, (100, 3))
        X[0][0] = np.nan
        return X

    else:
        raise ValueError("Invalid mode")


# -------------------------------
# PREDICTION (FAKE FOR NOW)
# -------------------------------
def predict(X):
    return model.predict(X)


# -------------------------------
# DATA QUALITY CHECKS
# -------------------------------
def run_data_quality_checks(db: Session, run: PipelineRun, X):
    if np.isnan(X).any():
        finding = DataQualityFinding(
            run_id=run.id,
            issue_type="missing",
            column_name="unknown",
            description="NaN values detected"
        )
        db.add(finding)


# -------------------------------
# DRIFT CHECKS
# -------------------------------
def run_drift_checks(db: Session, run: PipelineRun, X):
    baseline_mean = 0.5
    current_mean = float(np.mean(X))

    drift_score = abs(current_mean - baseline_mean)

    if drift_score > 0.2:
        finding = DriftFinding(
            run_id=run.id,
            feature_name="global_mean",
            drift_score=drift_score,
            drift_detected=True
        )
        db.add(finding)


# -------------------------------
# INCIDENT CREATION
# -------------------------------
def create_incidents(db: Session, run: PipelineRun):
    # Drift-based incidents
    for drift in run.drift_findings:
        if drift.drift_detected:
            db.add(Incident(
                run_id=run.id,
                title="Drift detected",
                description=f"{drift.feature_name} drifted",
                failure_type="drift",
                finding_type="drift",
                finding_id=drift.id,
                severity="high"
            ))

    # Data quality incidents
    for dq in run.data_quality_findings:
        db.add(Incident(
            run_id=run.id,
            title="Data quality issue",
            description=dq.description,
            failure_type="data_quality",
            finding_type="data_quality",
            finding_id=dq.id,
            severity="medium"
        ))


# -------------------------------
# MAIN PIPELINE FUNCTION
# -------------------------------
def run_pipeline(db: Session, model_id: int, mode: str = "bad"):

    run = PipelineRun(
        model_id=model_id,
        status="running",
        started_at=datetime.utcnow()
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    try:
        # 1. Generate Data
        X = generate_data(mode)

        # 2. Predict
        preds = predict(X)

        def clean_value(v):
            if isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
                return None
            return float(v)

        def clean_array(arr):
            return [clean_value(v) for v in arr]

        # 3. Store predictions
        for i in range(len(X)):
            db.add(PredictionLog(
                run_id=run.id,
                input_data=clean_array(X[i]),
                prediction=clean_value(preds[i])
            ))

        db.commit()

        # 4. Run Checks
        run_data_quality_checks(db, run, X)
        run_drift_checks(db, run, X)
        db.commit()

        # 5. Create Incidents
        create_incidents(db, run)
        db.commit()

        # 6. STATUS LOGIC (THIS WAS MISSING)
        drift_findings = db.query(DriftFinding).filter_by(run_id=run.id).all()
        data_findings = db.query(DataQualityFinding).filter_by(run_id=run.id).all()

        has_drift = any(d.drift_detected for d in drift_findings)
        has_data_issues = len(data_findings) > 0

        if has_drift or has_data_issues:
            run.status = "completed_with_issues"
        else:
            run.status = "completed"

    except Exception as e:
        print("[ERROR]", e)
        db.rollback()
        run.status = "failed"

    finally:
        run.ended_at = datetime.utcnow()
        db.commit()
        db.refresh(run)

    return run