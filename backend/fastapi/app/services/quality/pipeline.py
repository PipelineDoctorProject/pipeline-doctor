import pandas as pd
import os
from sqlalchemy.orm import Session

from app.services.quality.baseline_service import get_active_baseline
from app.services.quality.schema_handler import handle_schema
from app.services.quality.validator import DataValidator
from app.services.quality.pipeline_run_service import (
    create_pipeline_run,
    update_pipeline_run_status
)
from app.services.quality.storage import store_findings

from app.models.schema_change_event import SchemaChangeEvent


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
        df = pd.read_csv(file_path)

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
        # 7. UPDATE STATUS
        # --------------------------------------------------
        update_pipeline_run_status(db, run.id, "success")

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