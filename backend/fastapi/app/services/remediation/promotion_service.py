from __future__ import annotations

from typing import Any

from mlflow.tracking import MlflowClient
from sqlalchemy.orm import Session

from app.config import settings
from app.config.settings import resolve_mlflow_tracking_uri
from app.models.ml_model import MLModel
from app.models.remediation_action_log import RemediationActionLog
from app.services.quality.pipeline import clear_mlflow_model_cache


def get_candidate_result_for_run(
    db: Session,
    remediation_run_id: int,
) -> dict[str, Any] | None:
    logs = (
        db.query(RemediationActionLog)
        .filter(RemediationActionLog.remediation_run_id == remediation_run_id)
        .order_by(RemediationActionLog.id.desc())
        .all()
    )

    for log in logs:
        if isinstance(log.payload, dict) and log.payload.get("candidate_model_uri"):
            return dict(log.payload)

    return None


def promote_candidate_model(
    db: Session,
    model_record: MLModel,
    candidate_result: dict[str, Any],
    *,
    promoted_by: str,
    review_notes: str | None = None,
) -> dict[str, Any]:
    candidate_model_uri = candidate_result.get("candidate_model_uri")
    candidate_run_id = candidate_result.get("candidate_mlflow_run_id")
    if not candidate_model_uri or not candidate_run_id:
        raise ValueError("Candidate model artifacts are missing, so promotion cannot continue.")

    if not model_record.mlflow_model_name:
        raise ValueError(
            "This model is not linked to an MLflow registered model, so candidate promotion cannot continue."
        )

    tracking_uri = resolve_mlflow_tracking_uri(model_record.mlflow_tracking_uri)
    client = MlflowClient(tracking_uri=tracking_uri)

    try:
        client.get_registered_model(model_record.mlflow_model_name)
    except Exception:
        client.create_registered_model(model_record.mlflow_model_name)

    created_version = client.create_model_version(
        name=model_record.mlflow_model_name,
        source=candidate_model_uri,
        run_id=candidate_run_id,
    )

    promotion_alias = (model_record.mlflow_alias or settings.REMEDIATION_PROMOTION_ALIAS).strip()
    if not promotion_alias:
        promotion_alias = settings.REMEDIATION_PROMOTION_ALIAS

    client.set_registered_model_alias(
        name=model_record.mlflow_model_name,
        alias=promotion_alias,
        version=str(created_version.version),
    )

    model_record.version = str(created_version.version)
    model_record.mlflow_alias = promotion_alias
    model_record.mlflow_run_id = str(candidate_run_id)

    feature_columns = candidate_result.get("feature_columns")
    if isinstance(feature_columns, list) and feature_columns:
        model_record.expected_features = feature_columns

    db.add(model_record)
    clear_mlflow_model_cache(model_record.mlflow_model_name)

    promoted_model_uri = f"models:/{model_record.mlflow_model_name}@{promotion_alias}"
    promoted_model_version_uri = (
        f"models:/{model_record.mlflow_model_name}/{created_version.version}"
    )

    return {
        "candidate_model_uri": candidate_model_uri,
        "candidate_mlflow_run_id": candidate_run_id,
        "promoted_alias": promotion_alias,
        "promoted_model_name": model_record.mlflow_model_name,
        "promoted_model_version": str(created_version.version),
        "promoted_model_uri": promoted_model_uri,
        "promoted_model_version_uri": promoted_model_version_uri,
        "feature_columns": feature_columns,
        "feature_source": candidate_result.get("feature_source"),
        "metrics": candidate_result.get("metrics"),
        "review_notes": review_notes,
        "promoted_by": promoted_by,
    }
