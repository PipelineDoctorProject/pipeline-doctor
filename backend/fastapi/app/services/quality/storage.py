from sqlalchemy.orm import Session
from datetime import datetime

from app.models.data_quality import DataQualityFinding


def store_findings(
    db: Session,
    model_id: int,
    pipeline_run_id: int,
    result: dict,
    extra_cols: list,
    missing_cols: list
):
    findings = []

    # Column checks
    for check in result.get("checks", []):
        findings.append(
            DataQualityFinding(
                model_id=model_id,
                pipeline_run_id=pipeline_run_id,
                column_name=check.get("column"),
                check_type=check.get("check"),
                success=check.get("success"),
                details={"message": check.get("details")}
            )
        )

    # Schema findings
    if extra_cols:
        findings.append(
            DataQualityFinding(
                model_id=model_id,
                pipeline_run_id=pipeline_run_id,
                column_name=None,
                check_type="extra_columns",
                success=False,
                details={"columns": extra_cols}
            )
        )

    if missing_cols:
        findings.append(
            DataQualityFinding(
                model_id=model_id,
                pipeline_run_id=pipeline_run_id,
                column_name=None,
                check_type="missing_columns",
                success=False,
                details={"columns": missing_cols}
            )
        )

    db.add_all(findings)
    db.commit()