import pandas as pd
from sqlalchemy.orm import Session

from app.services.quality.baseline_service import get_active_baseline
from app.services.quality.schema_handler import handle_schema
from app.services.quality.validator import DataValidator



def run_data_quality_pipeline(db: Session, model_id: int, file_path: str):
    df = pd.read_csv(file_path)

    # get baseline
    baseline = get_active_baseline(db, model_id)

    schema = baseline.schema
    profile = baseline.profile

    # schema handling
    df, extra_cols, missing_cols = handle_schema(df, schema)

    # validation
    validator = DataValidator(df, {"schema": schema, "profile": profile})
    result = validator.run()

    # append schema issues
    if extra_cols:
        result["schema_errors"].append(f"Extra columns: {extra_cols}")
    if missing_cols:
        result["schema_errors"].append(f"Missing columns: {missing_cols}")

    return {
        "result": result,
        "cleaned_df": df,
        "extra_cols": extra_cols,
        "missing_cols": missing_cols
    }

from app.services.quality.pipeline_run_service import create_pipeline_run, update_pipeline_run_status


def run_data_quality_pipeline(db: Session, model_id: int, file_path: str):

    # 1. Get baseline FIRST
    baseline = get_active_baseline(db, model_id)

    # 2. Create pipeline run
    run = create_pipeline_run(
        db,
        model_id=model_id,
        baseline_version=baseline.version,
        file_path=file_path
    )

    try:
        # 3. Load data
        df = pd.read_csv(file_path)

        # 4. Schema handling
        df, extra_cols, missing_cols = handle_schema(df, baseline.schema)

        # 5. Validation
        validator = DataValidator(df, {
            "schema": baseline.schema,
            "profile": baseline.profile
        })

        result = validator.run()

        if extra_cols:
            result["schema_errors"].append(f"Extra columns: {extra_cols}")

        if missing_cols:
            result["schema_errors"].append(f"Missing columns: {missing_cols}")

        # 6. Mark success
        update_pipeline_run_status(db, run.id, "success")

        return {
            "run_id": run.id,
            "baseline_version": baseline.version,
            "result": result,
            "cleaned_df": df,
            "extra_cols": extra_cols,
            "missing_cols": missing_cols
        }

    except Exception as e:
        update_pipeline_run_status(db, run.id, "failed")
        raise e

