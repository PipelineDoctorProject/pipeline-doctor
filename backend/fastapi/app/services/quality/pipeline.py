import os
import math

import mlflow
import mlflow.pyfunc
import numpy
import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.config.settings import MLFLOW_TRACKING_URI, resolve_mlflow_tracking_uri
from app.models.ml_model import MLModel
from app.models.pipeline_run import PipelineRun
from app.models.prediction_log import PredictionLog
from app.models.schema_change_event import SchemaChangeEvent
from app.services.drift.drift_service import run_drift_checks
from app.services.quality.baseline_service import get_active_baseline
from app.services.quality.data_loader import load_dataset
from app.services.quality.pipeline_run_service import (
    create_pipeline_run,
    update_pipeline_run_fields,
    update_pipeline_run_status,
)
from app.services.quality.schema_handler import handle_schema
from app.services.quality.schema_evolution import build_feature_candidates
from app.services.quality.storage import store_findings
from app.services.file_storage import store_dataframe_csv
from app.services.quality.transformer import DataTransformer
from app.services.quality.validator import DataValidator

# MLflow Config
mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
_model_cache = {}


def clear_mlflow_model_cache(model_name: str | None = None):
    if not model_name:
        _model_cache.clear()
        return

    target_prefix = f"{model_name}@"
    stale_keys = [
        cache_key
        for cache_key in list(_model_cache.keys())
        if cache_key.startswith(target_prefix)
    ]
    for cache_key in stale_keys:
        _model_cache.pop(cache_key, None)


def get_mlflow_model(db: Session, model_id: int):
    db_model = db.query(MLModel).filter(MLModel.id == model_id).first()
    if not db_model or not db_model.mlflow_model_name:
        return None, None

    cache_key = f"{db_model.mlflow_model_name}@{db_model.mlflow_alias or 'champion'}"
    if cache_key not in _model_cache:
        try:
            if db_model.mlflow_tracking_uri:
                mlflow.set_tracking_uri(
                    resolve_mlflow_tracking_uri(db_model.mlflow_tracking_uri)
                )
            else:
                mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

            uri = (
                f"models:/{db_model.mlflow_model_name}"
                f"@{db_model.mlflow_alias or 'champion'}"
            )
            _model_cache[cache_key] = mlflow.pyfunc.load_model(uri)
        except Exception as exc:
            print(f"Warning: Could not load MLflow model {cache_key}: {exc}")
            _model_cache[cache_key] = None

    return _model_cache[cache_key], db_model


def clean_value(value):
    try:
        value = float(value)
        if numpy.isnan(value) or numpy.isinf(value):
            return None
        return value
    except Exception:
        return None


def clean_array(values):
    return [clean_value(value) for value in values]


def to_python_types(obj):
    import numpy as np

    if isinstance(obj, dict):
        return {key: to_python_types(value) for key, value in obj.items()}
    if isinstance(obj, list):
        return [to_python_types(value) for value in obj]
    if isinstance(obj, tuple):
        return [to_python_types(value) for value in obj]
    if obj is None:
        return None
    if isinstance(obj, float):
        return obj if math.isfinite(obj) else None
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        value = float(obj)
        return value if math.isfinite(value) else None
    if isinstance(obj, pd.Series):
        return [to_python_types(value) for value in obj.tolist()]
    if isinstance(obj, pd.Index):
        return [to_python_types(value) for value in obj.tolist()]
    if isinstance(obj, np.ndarray):
        return [to_python_types(value) for value in obj.tolist()]
    try:
        if pd.isna(obj):
            return None
    except TypeError:
        pass
    return obj


def _resolve_doctor_tenant_id(
    db: Session,
    model_id: int,
    current_tenant_id: str | None = None,
):
    if current_tenant_id:
        return current_tenant_id

    tenant_id = db.execute(
        text("SELECT tenant_id FROM public.ml_models WHERE id = :model_id"),
        {"model_id": model_id},
    ).scalar()

    if tenant_id:
        return tenant_id

    model_record = db.query(MLModel).filter(MLModel.id == model_id).first()
    return model_record.tenant_id if model_record else None


def _build_cleaned_path(run_id: int) -> str:
    return os.path.join(settings.CLEANED_OUTPUT_DIR, f"{run_id}.csv")


def _build_quarantine_path(run_id: int) -> str:
    return os.path.join(settings.QUARANTINE_OUTPUT_DIR, f"{run_id}.csv")


def _write_dataframe(df: pd.DataFrame, path: str):
    return store_dataframe_csv(df, path)


def _append_schema_change_annotations(
    result: dict,
    extra_cols: list[str],
    missing_cols: list[str],
) -> dict:
    annotated = {
        "schema_errors": list(result.get("schema_errors", [])),
        "checks": list(result.get("checks", [])),
        "summary": dict(result.get("summary", {})),
    }

    if extra_cols:
        annotated["schema_errors"].append(f"Extra columns: {extra_cols}")

    if missing_cols:
        annotated["schema_errors"].append(f"Missing columns: {missing_cols}")

    if extra_cols or missing_cols:
        annotated["summary"]["status"] = "FAIL"

    return annotated


def _evaluate_quality_gate(
    cleaned_rows: int,
    total_rows: int,
    post_clean_result: dict,
    missing_cols: list[str],
) -> dict:
    blocking_reasons: list[str] = []

    if missing_cols:
        blocking_reasons.append(
            "The incoming dataset is missing baseline-required columns and cannot "
            "be treated as production-safe input."
        )

    if cleaned_rows == 0:
        blocking_reasons.append("No usable rows remained after cleaning.")

    if cleaned_rows < settings.DATA_QUALITY_MIN_CLEAN_ROW_COUNT:
        blocking_reasons.append(
            "The cleaned dataset is below the minimum accepted row count "
            f"({cleaned_rows} < {settings.DATA_QUALITY_MIN_CLEAN_ROW_COUNT})."
        )

    clean_row_ratio = float(cleaned_rows / total_rows) if total_rows else 0.0
    if total_rows and clean_row_ratio < settings.DATA_QUALITY_MIN_CLEAN_ROW_RATIO:
        blocking_reasons.append(
            "The cleaned dataset retained too few rows after quarantine "
            f"({clean_row_ratio:.2%} < "
            f"{settings.DATA_QUALITY_MIN_CLEAN_ROW_RATIO:.0%})."
        )

    if post_clean_result.get("schema_errors"):
        blocking_reasons.append(
            "The cleaned dataset still has schema/type mismatches after coercion."
        )

    failed_checks = int(post_clean_result.get("summary", {}).get("failed_checks", 0))
    if failed_checks > 0:
        blocking_reasons.append(
            f"The cleaned dataset still failed {failed_checks} validation checks."
        )

    pipeline_status = "success" if not blocking_reasons else "failed"
    return {
        "status": pipeline_status,
        "blocking_reasons": blocking_reasons,
        "clean_row_count": cleaned_rows,
        "clean_row_ratio": clean_row_ratio,
        "min_clean_row_count": settings.DATA_QUALITY_MIN_CLEAN_ROW_COUNT,
        "min_clean_row_ratio": settings.DATA_QUALITY_MIN_CLEAN_ROW_RATIO,
    }


def _generate_predictions(
    db: Session,
    model_id: int,
    run_id: int,
    df: pd.DataFrame,
):
    
    model, db_model = get_mlflow_model(db, model_id)
    if model is None:
        print("MLflow model not loaded. Skipping predictions.")
        return {"status": "skipped", "reason": "model_not_loaded"}

    try:
        print(f"Generating predictions for run {run_id}...")

        if db_model.expected_features:
            current_cols = {col.lower(): col for col in df.columns}
            missing_features = [
                feature
                for feature in db_model.expected_features
                if feature.lower() not in current_cols
            ]
            if missing_features:
                print(
                    "Warning: Missing expected features for model prediction: "
                    f"{missing_features}"
                )

            safe_features = [
                current_cols[feature.lower()]
                for feature in db_model.expected_features
                if feature.lower() in current_cols
            ]
            X_for_prediction = (
                df[safe_features]
                .fillna(0.0)
                .astype(numpy.float64)
            )
        else:
            numeric_df = df.select_dtypes(include=[numpy.number])
            if len(numeric_df.columns) >= 3:
                X_for_prediction = numeric_df.iloc[:, :3].fillna(0.0)
            else:
                X_for_prediction = numeric_df.fillna(0.0)

        preds = model.predict(X_for_prediction)

        prediction_logs = []
        for idx in range(len(df)):
            row_features = df.iloc[idx].tolist()
            pred_val = preds[idx] if hasattr(preds, "__getitem__") else preds.iloc[idx]
            prediction_logs.append(
                PredictionLog(
                    run_id=run_id,
                    input_data={"features": clean_array(row_features)},
                    prediction={"value": clean_value(pred_val)},
                )
            )

        db.add_all(prediction_logs)
        db.commit()
        print("Predictions generated and saved.")
        return {"status": "generated", "count": len(prediction_logs)}
    except Exception as exc:
        print(f"Prediction generation failed: {exc}")
        db.rollback()
        return {"status": "failed", "reason": str(exc)}


def _queue_root_cause_analysis(
    db: Session,
    model_id: int,
    run_id: int,
    current_tenant_id: str | None = None,
):
    try:
        print(f"Queueing doctor agent RCA for run {run_id}...")
        tenant_id = _resolve_doctor_tenant_id(
            db=db,
            model_id=model_id,
            current_tenant_id=current_tenant_id,
        )
        if not tenant_id:
            raise Exception("Tenant id could not be resolved for the doctor agent task")

        from app.tasks.ai_tasks import run_doctor_agent_task

        run_doctor_agent_task.apply_async(
            args=(run_id, tenant_id, "doctor"),
            expires=300,
        )
        print("Doctor agent RCA queued.")
        return {
            "status": "queued",
            "message": "Doctor agent RCA has been queued and will generate trace logs.",
        }
    except Exception as exc:
        db.rollback()
        print(f"Doctor agent RCA queue encountered an error: {exc}")
        return {
            "status": "failed",
            "message": str(exc),
        }


def run_data_quality_pipeline(
    db: Session,
    model_id: int,
    file_path: str,
    current_tenant_id: str | None = None,
):
    baseline = get_active_baseline(db, model_id)

    run = create_pipeline_run(
        db,
        model_id=model_id,
        baseline_version=baseline.version,
        file_path=file_path,
    )
    run_id = run.id

    try:
        df = load_dataset(file_path)
        total_rows = int(len(df))

        incoming_cols = set(df.columns)
        baseline_cols = set(baseline.schema.keys())
        extra_cols = sorted(list(incoming_cols - baseline_cols))
        missing_cols = sorted(list(baseline_cols - incoming_cols))

        schema_event = None
        if extra_cols or missing_cols:
            existing_event = (
                db.query(SchemaChangeEvent)
                .filter(
                    SchemaChangeEvent.model_id == model_id,
                    SchemaChangeEvent.status == "pending",
                )
                .first()
            )

            if existing_event:
                schema_event = existing_event
                if extra_cols and not schema_event.feature_candidates:
                    schema_event.feature_candidates = build_feature_candidates(df, extra_cols)
                    db.add(schema_event)
                    db.commit()
            else:
                schema_event = SchemaChangeEvent(
                    model_id=model_id,
                    pipeline_run_id=run_id,
                    baseline_id=baseline.id,
                    new_columns=extra_cols,
                    missing_columns=missing_cols,
                    feature_candidates=build_feature_candidates(df, extra_cols),
                    status="pending",
                )
                db.add(schema_event)
                db.commit()
                db.refresh(schema_event)

        update_pipeline_run_fields(
            db,
            run_id,
            schema_changed=bool(extra_cols or missing_cols),
        )

        aligned_df, _, _ = handle_schema(df, baseline.schema)

        raw_validation_result = DataValidator(
            aligned_df,
            {"schema": baseline.schema, "profile": baseline.profile},
        ).run()
        raw_validation_result = _append_schema_change_annotations(
            raw_validation_result,
            extra_cols,
            missing_cols,
        )

        transformer = DataTransformer(
            aligned_df,
            baseline.schema,
            baseline.profile,
        )
        cleaned_df, cleaning_report = transformer.run()

        cleaned_path = _build_cleaned_path(run_id)
        quarantine_path = _build_quarantine_path(run_id)
        cleaned_path = _write_dataframe(cleaned_df, cleaned_path)

        quarantine_written = False
        if not transformer.removed_rows.empty:
            quarantine_path = _write_dataframe(transformer.removed_rows, quarantine_path)
            quarantine_written = True

        update_pipeline_run_fields(db, run_id, cleaned_data_path=cleaned_path)

        post_clean_result = DataValidator(
            cleaned_df,
            {"schema": baseline.schema, "profile": baseline.profile},
        ).run()

        store_findings(
            db,
            model_id,
            run_id,
            raw_validation_result,
            extra_cols,
            missing_cols,
        )

        quality_gate = _evaluate_quality_gate(
            cleaned_rows=int(len(cleaned_df)),
            total_rows=total_rows,
            post_clean_result=post_clean_result,
            missing_cols=missing_cols,
        )

        prediction_status = {"status": "skipped", "reason": "validation_failed"}
        drift_status = {
            "status": "skipped",
            "reason": "validation_failed",
        }

        if quality_gate["status"] == "success":
            prediction_status = _generate_predictions(
                db=db,
                model_id=model_id,
                run_id=run_id,
                df=cleaned_df,
            )
            update_pipeline_run_status(db, run_id, "success")

            try:
                print(f"Running drift checks for run {run_id}...")
                run_for_drift = db.get(PipelineRun, run_id, populate_existing=True)
                if not run_for_drift:
                    raise Exception("Pipeline run not found for drift checks")

                drift_result = run_drift_checks(
                    db,
                    run_for_drift,
                    tenant_id=current_tenant_id,
                )
                print(f"Drift checks completed: {drift_result}")
                drift_status = {"status": "completed", "result": drift_result}
            except Exception as exc:
                db.rollback()
                import traceback

                print(f"Drift checks encountered an error: {exc}")
                traceback.print_exc()
                drift_status = {"status": "failed", "reason": str(exc)}
        else:
            update_pipeline_run_status(db, run_id, "failed")
            print(
                f"Validation gate blocked run {run_id}: "
                f"{quality_gate['blocking_reasons']}"
            )

        root_cause_status = _queue_root_cause_analysis(
            db=db,
            model_id=model_id,
            run_id=run_id,
            current_tenant_id=current_tenant_id,
        )

        response = {
            "run_id": int(run_id),
            "baseline_version": int(baseline.version),
            "pipeline_status": quality_gate["status"],
            "cleaned_data_path": cleaned_path,
            "quarantine_data_path": quarantine_path if quarantine_written else None,
            "result": raw_validation_result,
            "post_clean_validation": post_clean_result,
            "cleaning_report": {
                **cleaning_report,
                "quarantine_written": quarantine_written,
            },
            "quality_gate": quality_gate,
            "prediction_status": prediction_status,
            "drift_status": drift_status,
            "schema_change_detected": bool(extra_cols or missing_cols),
            "new_columns": extra_cols,
            "missing_columns": missing_cols,
            "schema_event_id": int(schema_event.id) if schema_event else None,
            "action": "awaiting_approval" if schema_event else "none",
            "root_cause_analysis": root_cause_status,
        }

        return to_python_types(response)
    except Exception:
        db.rollback()
        try:
            update_pipeline_run_status(db, run_id, "failed")
        except Exception as status_exc:
            print(f"Could not mark run {run_id} as failed: {status_exc}")
        raise
