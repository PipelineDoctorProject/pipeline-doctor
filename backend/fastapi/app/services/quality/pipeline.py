import pandas as pd
from sqlalchemy.orm import Session

from app.models.baseline import Baseline
from app.services.quality.validator import DataValidator
from app.services.quality.schema_handler import handle_schema
from app.services.quality.baseline_service import get_active_baseline

def run_data_quality_pipeline(
    db: Session,
    model_id: int,
    file_path: str
):
    # 1. Load data
    df = pd.read_csv(file_path)

    # 2. Get latest APPROVED baseline
    baseline = get_active_baseline(db, model_id)

    if not baseline:
        raise ValueError("Baseline not found")

    baseline_schema = baseline.schema
    baseline_profile = baseline.profile

    # 3. Handle schema differences
    aligned_df, extra_cols, missing_cols = handle_schema(df, baseline_schema)

    # 4. Run validation
    validator = DataValidator(
        aligned_df,
        {
            "schema": baseline_schema,
            "profile": baseline_profile
        }
    )
    result = validator.run()

    # 5. Add schema issues to result
    if extra_cols:
        result["schema_errors"].append(f"Extra columns: {extra_cols}")

    if missing_cols:
        result["schema_errors"].append(f"Missing columns: {missing_cols}")

    # 6. Safe cleaning (minimal)
    cleaned_df = aligned_df.copy()

    return {
        "result": result,
        "cleaned_df": cleaned_df,
        "extra_cols": extra_cols,
        "missing_cols": missing_cols
    }