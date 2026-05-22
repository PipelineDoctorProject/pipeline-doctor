import pandas as pd
import os
from sqlalchemy.orm import Session
import numpy
from app.services.quality.baseline_service import get_active_baseline
from app.services.quality.schema_handler import handle_schema
from app.services.quality.validator import DataValidator
from app.services.quality.pipeline_run_service import (
    create_pipeline_run,
    update_pipeline_run_fields,
    update_pipeline_run_status
)
from app.services.quality.storage import store_findings
from app.services.quality.transformer import DataTransformer
from app.models.schema_change_event import SchemaChangeEvent
from app.models.ml_model import MLModel
from app.services.quality.data_loader import load_dataset
from app.services.drift.drift_service import run_drift_checks
from app.models.pipeline_run import PipelineRun
from app.models.prediction_log import PredictionLog
import mlflow
import mlflow.pyfunc
from app.config.settings import MLFLOW_TRACKING_URI, resolve_mlflow_tracking_uri

# MLflow Config
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
_model_cache = {}

def get_mlflow_model(db: Session, model_id: int):
    from app.models.ml_model import MLModel
    db_model = db.query(MLModel).filter(MLModel.id == model_id).first()
    if not db_model or not db_model.mlflow_model_name:
        return None, None
        
    cache_key = f"{db_model.mlflow_model_name}@{db_model.mlflow_alias or 'champion'}"
    if cache_key not in _model_cache:
        try:
            # Set the tracking URI dynamically based on the model's configuration
            if db_model.mlflow_tracking_uri:
                mlflow.set_tracking_uri(
                    resolve_mlflow_tracking_uri(db_model.mlflow_tracking_uri)
                )
            else:
                # Default fallback shared by local and container runs.
                mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
                
            uri = f"models:/{db_model.mlflow_model_name}@{db_model.mlflow_alias or 'champion'}"
            _model_cache[cache_key] = mlflow.pyfunc.load_model(uri)
        except Exception as e:
            print(f"Warning: Could not load MLflow model {cache_key}: {e}")
            _model_cache[cache_key] = None
            
    return _model_cache[cache_key], db_model

def clean_value(v):
    try:
        v = float(v)
        if numpy.isnan(v) or numpy.isinf(v):
            return None
        return v
    except Exception:
        return None

def clean_array(arr):
    return [clean_value(v) for v in arr]

# --------------------------------------------------
# 🔥 GLOBAL SAFE CONVERTER (CRITICAL FIX)
# --------------------------------------------------
def to_python_types(obj):
    import numpy as np

    if isinstance(obj, dict):
        return {k: to_python_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [to_python_types(v) for v in obj]
    elif isinstance(obj, (np.bool_,)):
        return bool(obj)
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    else:
        return obj


# --------------------------------------------------
# 🚀 MAIN PIPELINE
# --------------------------------------------------
def run_data_quality_pipeline(db: Session, model_id: int, file_path: str):

    baseline = get_active_baseline(db, model_id)

    run = create_pipeline_run(
        db,
        model_id=model_id,
        baseline_version=baseline.version,
        file_path=file_path
    )
    run_id = run.id

    try:
        # --------------------------------------------------
        # 1. LOAD DATA
        # --------------------------------------------------
        df = load_dataset(file_path)

        # --------------------------------------------------
        # 2. SCHEMA DETECTION (BEFORE MUTATION)
        # --------------------------------------------------
        incoming_cols = set(df.columns)
        baseline_cols = set(baseline.schema.keys())

        extra_cols = sorted(list(incoming_cols - baseline_cols))
        missing_cols = sorted(list(baseline_cols - incoming_cols))

        schema_event = None

        if extra_cols:
            # 🔒 deduplication (simple version)
            existing_event = (
                db.query(SchemaChangeEvent)
                .filter(
                    SchemaChangeEvent.model_id == model_id,
                    SchemaChangeEvent.status == "pending"
                )
                .first()
            )

            if existing_event:
                schema_event = existing_event
            else:
                schema_event = SchemaChangeEvent(
                    model_id=model_id,
                    pipeline_run_id=run_id,
                    baseline_id=baseline.id,
                    new_columns=extra_cols,
                    missing_columns=missing_cols,
                    status="pending"
                )
                db.add(schema_event)
                db.commit()
                db.refresh(schema_event)

            # mark run
            update_pipeline_run_fields(db, run_id, schema_changed=True)
        else:
            update_pipeline_run_fields(db, run_id, schema_changed=False)

        # --------------------------------------------------
        # 3. SCHEMA HANDLING (NO DATA LOSS CHANGE)
        # --------------------------------------------------
        df, _, _ = handle_schema(df, baseline.schema)

        # --------------------------------------------------
        # 4. VALIDATION
        # --------------------------------------------------
        validator = DataValidator(df, {
            "schema": baseline.schema,
            "profile": baseline.profile
        })

        result = validator.run()
        transformer = DataTransformer(
                df,
                baseline.schema
            )

        df = transformer.run()

        if extra_cols:
            result["schema_errors"].append(f"Extra columns: {extra_cols}")

        if missing_cols:
            result["schema_errors"].append(f"Missing columns: {missing_cols}")

        # --------------------------------------------------
        # 5. SAVE CLEANED DATA
        # --------------------------------------------------
        os.makedirs("cleaned", exist_ok=True)

        cleaned_path = f"cleaned/{run_id}.csv"
        df.to_csv(cleaned_path, index=False)

        update_pipeline_run_fields(db, run_id, cleaned_data_path=cleaned_path)

        # --------------------------------------------------
        # 6. STORE FINDINGS
        # --------------------------------------------------
        store_findings(
            db,
            model_id,
            run_id,
            result,
            extra_cols,
            missing_cols
        )

        # --------------------------------------------------
        # 6.5. GENERATE PREDICTIONS
        # --------------------------------------------------
        model, db_model = get_mlflow_model(db, model_id)
        if model is not None:
            try:
                print(f"Generating predictions for run {run_id}...")
                
                if db_model.expected_features:
                    # Case-insensitive column matching
                    current_cols = {c.lower(): c for c in df.columns}
                    expected_lower = [f.lower() for f in db_model.expected_features]
                    
                    missing_features = [f for f in db_model.expected_features if f.lower() not in current_cols]
                    if missing_features:
                        print(f"Warning: Missing expected features for model prediction: {missing_features}")
                    
                    # Fill na, enforce column order, and cast to float64 for MLflow compatibility
                    safe_features = [current_cols[f.lower()] for f in db_model.expected_features if f.lower() in current_cols]
                    X_for_prediction = df[safe_features].fillna(0.0).astype(numpy.float64)
                else:
                    # Fallback for the demo: The mock MLflow model expects exactly 3 numeric features (shape -1, 3)
                    numeric_df = df.select_dtypes(include=[numpy.number])
                    if len(numeric_df.columns) >= 3:
                        X_for_prediction = numeric_df.iloc[:, :3].fillna(0.0)
                    else:
                        X_for_prediction = numeric_df.fillna(0.0)
                        
                preds = model.predict(X_for_prediction)
                
                prediction_logs = []
                for i in range(len(df)):
                    row_features = df.iloc[i].tolist()
                    pred_val = preds[i] if hasattr(preds, '__getitem__') else preds.iloc[i]
                    prediction_logs.append(PredictionLog(
                        run_id=run_id,
                        input_data={"features": clean_array(row_features)},
                        prediction={"value": clean_value(pred_val)}
                    ))
                db.add_all(prediction_logs)
                db.commit()
                print("Predictions generated and saved.")
            except Exception as pred_e:
                print(f"Prediction generation failed: {pred_e}")
                db.rollback()
        else:
            print("MLflow model not loaded. Skipping predictions.")

        # --------------------------------------------------
        # 7. UPDATE STATUS
        # --------------------------------------------------
        update_pipeline_run_status(db, run_id, "success")

        # --------------------------------------------------
        # 7.5. RUN DRIFT DETECTION
        # --------------------------------------------------
        try:
            print(f"Running drift checks for run {run_id}...")
            run_for_drift = db.get(PipelineRun, run_id, populate_existing=True)
            if not run_for_drift:
                raise Exception("Pipeline run not found for drift checks")
            drift_result = run_drift_checks(db, run_for_drift)
            print(f"Drift checks completed: {drift_result}")
        except Exception as drift_e:
            db.rollback()
            import traceback
            print(f"Drift checks encountered an error: {drift_e}")
            traceback.print_exc()

        root_cause_status = None
        try:
            print(f"Queueing doctor agent RCA for run {run_id}...")
            model_record = (
                db.query(MLModel)
                .filter(MLModel.id == model_id)
                .first()
            )
            tenant_id = model_record.tenant_id if model_record else None
            if not tenant_id:
                raise Exception("Tenant id could not be resolved for the doctor agent task")

            # Import locally to avoid startup-order issues with Celery task registration.
            from app.tasks.ai_tasks import run_doctor_agent_task

            run_doctor_agent_task.apply_async(
                args=(run_id, tenant_id, "doctor"),
                expires=300,
            )
            root_cause_status = {
                "status": "queued",
                "message": "Doctor agent RCA has been queued and will generate trace logs.",
            }
            print("Doctor agent RCA queued.")
        except Exception as ai_e:
            db.rollback()
            print(f"Doctor agent RCA queue encountered an error: {ai_e}")

        # --------------------------------------------------
        # 8. SAFE RESPONSE (CRITICAL FIX)
        # --------------------------------------------------
        response = {
            "run_id": int(run_id),
            "baseline_version": int(baseline.version),
            "cleaned_data_path": cleaned_path,
            "result": result,

            "schema_change_detected": bool(extra_cols or missing_cols),
            "new_columns": extra_cols,
            "missing_columns": missing_cols,
            "schema_event_id": int(schema_event.id) if schema_event else None,
            "action": "awaiting_approval" if schema_event else "none",
            "root_cause_analysis": root_cause_status,
        }

        return to_python_types(response)

    except Exception as e:
        db.rollback()
        try:
            update_pipeline_run_status(db, run_id, "failed")
        except Exception as status_e:
            print(f"Could not mark run {run_id} as failed: {status_e}")
        raise e
