from datetime import datetime
from sqlalchemy.orm import Session
from app.models.data_quality import DataQualityFinding

    
def store_findings(db: Session, model_id: int, run_id: int, result, extra_cols, missing_cols):

    records = []

    for check in result.get("checks", []):
        details = {"info": check["details"]}
        if check.get("metadata"):
            details.update(check["metadata"])

        records.append(
            DataQualityFinding(
                model_id=model_id,
                pipeline_run_id=run_id,
                column_name=check["column"],
                check_type=check["check"],
                success=check["success"],
                details=details,
                created_at=datetime.utcnow(),
            )
        )

    for error in result.get("schema_errors", []):
        if error.startswith("Extra columns:") or error.startswith("Missing columns:"):
            continue

        column_name = error.split(":", 1)[0] if ":" in error else None
        details = {"info": error}

        if ": expected " in error and ", got " in error:
            expected = error.split(": expected ", 1)[1].split(", got ", 1)[0]
            actual = error.rsplit(", got ", 1)[1]
            details.update({"expected_type": expected, "actual_type": actual})

        records.append(
            DataQualityFinding(
                model_id=model_id,
                pipeline_run_id=run_id,
                column_name=column_name,
                check_type="schema_type_mismatch",
                success=False,
                details=details,
                created_at=datetime.utcnow(),
            )
        )

    if extra_cols:
        records.append(
            DataQualityFinding(
                model_id=model_id,
                pipeline_run_id=run_id,
                column_name=None,
                check_type="extra_columns",
                success=False,
                details={"columns": extra_cols},
                created_at=datetime.utcnow(),
            )
        )

    if missing_cols:
        records.append(
            DataQualityFinding(
                model_id=model_id,
                pipeline_run_id=run_id,
                column_name=None,
                check_type="missing_columns",
                success=False,
                details={"columns": missing_cols},
                created_at=datetime.utcnow(),
            )
        )

    db.add_all(records)
    db.commit()
