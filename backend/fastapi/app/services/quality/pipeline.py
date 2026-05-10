import pandas as pd
import os
from sqlalchemy.orm import Session
import numpy
from app.services.quality.baseline_service import get_active_baseline
from app.services.quality.schema_handler import handle_schema
from app.services.quality.validator import DataValidator
from app.services.quality.pipeline_run_service import (
    create_pipeline_run,
    update_pipeline_run_status
)
from app.services.quality.storage import store_findings
from app.services.quality.transformer import DataTransformer
from app.models.schema_change_event import SchemaChangeEvent
from app.services.quality.data_loader import load_dataset
from app.services.drift.drift_service import run_drift_checks
from app.models.prediction_log import PredictionLog
import mlflow
import mlflow.pyfunc

# MLflow Config
mlflow.set_tracking_uri("http://127.0.0.1:5000")
MODEL_URI = "models:/PipelineDoctorDemoModel@champion"
try:
    model = mlflow.pyfunc.load_model(MODEL_URI)
except Exception as e:
    print(f"Warning: Could not load MLflow model: {e}")
    model = None

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
                    pipeline_run_id=run.id,
                    baseline_id=baseline.id,
                    new_columns=extra_cols,
                    missing_columns=missing_cols,
                    status="pending"
                )
                db.add(schema_event)
                db.commit()
                db.refresh(schema_event)

            # mark run
            run.schema_changed = True
            db.commit()
        else:
            run.schema_changed = False
            db.commit()

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

        cleaned_path = f"cleaned/{run.id}.csv"
        df.to_csv(cleaned_path, index=False)

        run.cleaned_data_path = cleaned_path
        db.commit()

        # --------------------------------------------------
        # 6. STORE FINDINGS
        # --------------------------------------------------
        store_findings(
            db,
            model_id,
            run.id,
            result,
            extra_cols,
            missing_cols
        )

        # --------------------------------------------------
        # 6.5. GENERATE PREDICTIONS
        # --------------------------------------------------
        if model is not None:
            try:
                print(f"Generating predictions for run {run.id}...")
                X_for_prediction = df.fillna(0.0)
                preds = model.predict(X_for_prediction)
                
                prediction_logs = []
                for i in range(len(df)):
                    row_features = df.iloc[i].tolist()
                    pred_val = preds[i] if hasattr(preds, '__getitem__') else preds.iloc[i]
                    prediction_logs.append(PredictionLog(
                        run_id=run.id,
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
        update_pipeline_run_status(db, run.id, "success")

        # --------------------------------------------------
        # 7.5. RUN DRIFT DETECTION
        # --------------------------------------------------
        try:
            print(f"Running drift checks for run {run.id}...")
            run_drift_checks(db, run)
            print("Drift checks completed.")
        except Exception as drift_e:
            print(f"Drift checks encountered an error: {drift_e}")

        # --------------------------------------------------
        # 8. SAFE RESPONSE (CRITICAL FIX)
        # --------------------------------------------------
        response = {
            "run_id": int(run.id),
            "baseline_version": int(baseline.version),
            "cleaned_data_path": cleaned_path,
            "result": result,

            "schema_change_detected": bool(extra_cols),
            "new_columns": extra_cols,
            "missing_columns": missing_cols,
            "schema_event_id": int(schema_event.id) if schema_event else None,
            "action": "awaiting_approval" if schema_event else "none"
        }

        return to_python_types(response)

    except Exception as e:
        update_pipeline_run_status(db, run.id, "failed")
        raise e