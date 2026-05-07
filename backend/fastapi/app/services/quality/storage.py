from sqlalchemy.orm import Session
from app.models.data_quality import DataQualityFinding


def store_findings(db: Session, model_id: int, run_id: int, result, extra_cols, missing_cols):
    records = []

    for check in result.get("checks", []):
        records.append(
            DataQualityFinding(
                model_id=model_id,
                pipeline_run_id=run_id,
                column_name=check["column"],
                check_type=check["check"],
                success=check["success"],
                details={"info": check["details"]}
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
                details={"columns": extra_cols}
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
                details={"columns": missing_cols}
            )
        )

    db.add_all(records)
    db.commit()