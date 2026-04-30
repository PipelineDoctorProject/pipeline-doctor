from datetime import datetime
from sqlalchemy.orm import Session
import numpy as np
import mlflow
import mlflow.pyfunc

from app.models.pipeline_run import PipelineRun
from app.models.prediction_log import PredictionLog
from app.models.drift_finding import DriftFinding
from app.models.data_quality import DataQualityFinding
from app.models.incident import Incident


mlflow.set_tracking_uri("http://127.0.0.1:5000")

# model details
MODEL_URI = "models:/PipelineDoctorDemoModel@champion"
model = mlflow.pyfunc.load_model(MODEL_URI)


def generate_data(mode: str = "bad"):
    if mode == "normal":
        return np.random.normal(0.5, 0.1, (100, 3))

    if mode == "drift":
        return np.random.normal(0.9, 0.1, (100, 3))

    if mode == "bad":
        X = np.random.normal(0.5, 0.1, (100, 3))
        X[0][0] = np.nan
        return X

    raise ValueError("Invalid mode")


def predict(X):
    return model.predict(X)


def run_data_quality_checks(db: Session, run: PipelineRun, X):
    if np.isnan(X).any():
        db.add(DataQualityFinding(
            run_id=run.id,
            issue_type="missing",
            column_name="unknown",
            description="NaN values detected"
        ))


def run_drift_checks(db: Session, run: PipelineRun, X):
    baseline_mean = 0.5
    current_mean = float(np.nanmean(X))
    drift_score = abs(current_mean - baseline_mean)

    if drift_score > 0.2:
        db.add(DriftFinding(
            run_id=run.id,
            feature_name="global_mean",
            drift_score=drift_score,
            drift_detected=True
        ))


def create_incidents(db: Session, run: PipelineRun):
    drift_findings = db.query(DriftFinding).filter_by(run_id=run.id).all()
    data_quality_findings = db.query(DataQualityFinding).filter_by(run_id=run.id).all()

    for drift in drift_findings:
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

    for dq in data_quality_findings:
        db.add(Incident(
            run_id=run.id,
            title="Data quality issue",
            description=dq.description,
            failure_type="data_quality",
            finding_type="data_quality",
            finding_id=dq.id,
            severity="medium"
        ))


def clean_value(v):
    try:
        v = float(v)
        if np.isnan(v) or np.isinf(v):
            return None
        return v
    except Exception:
        return None


def clean_array(arr):
    return [clean_value(v) for v in arr]


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
        print("MODEL URI:", MODEL_URI)
        print("MODEL RUN ID:", model.metadata.run_id)
        X = generate_data(mode)

        X_for_prediction = np.nan_to_num(X, nan=0.0)
        preds = predict(X_for_prediction)

        for i in range(len(X)):
            db.add(PredictionLog(
                run_id=run.id,
                input_data={"features": clean_array(X[i])},
                prediction={"value": clean_value(preds[i])}
            ))

        db.commit()

        run_data_quality_checks(db, run, X)
        run_drift_checks(db, run, X)
        db.commit()

        create_incidents(db, run)
        db.commit()

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