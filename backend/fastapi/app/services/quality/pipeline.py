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


def run_data_quality_pipeline(db: Session, model_id: int, file_path: str):

    baseline = get_active_baseline(db, model_id)

    run = create_pipeline_run(
        db,
        model_id=model_id,
        baseline_version=baseline.version,
        file_path=file_path
    )

    try:
        # 1. Load data
        df = pd.read_csv(file_path)

        # 2. Schema handling
        df, extra_cols, missing_cols = handle_schema(df, baseline.schema)

        # 3. Validation
        validator = DataValidator(df, {
            "schema": baseline.schema,
            "profile": baseline.profile
        })

        result = validator.run()

        if extra_cols:
            result["schema_errors"].append(f"Extra columns: {extra_cols}")

        if missing_cols:
            result["schema_errors"].append(f"Missing columns: {missing_cols}")

        # 4. SAVE CLEANED DATA (FIXED)
        os.makedirs("cleaned", exist_ok=True)

        cleaned_path = f"cleaned/{run.id}.csv"
        df.to_csv(cleaned_path, index=False)

        run.cleaned_data_path = cleaned_path
        db.commit()

        # 5. STORE FINDINGS
        store_findings(
            db,
            model_id,
            run.id,
            result,
            extra_cols,
            missing_cols
        )

        # 6. UPDATE STATUS
        update_pipeline_run_status(db, run.id, "success")

        return {
            "run_id": run.id,
            "baseline_version": baseline.version,
            "cleaned_data_path": cleaned_path,
            "result": result
        }

    except Exception as e:
        update_pipeline_run_status(db, run.id, "failed")
        raise e