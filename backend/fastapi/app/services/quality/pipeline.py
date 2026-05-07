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