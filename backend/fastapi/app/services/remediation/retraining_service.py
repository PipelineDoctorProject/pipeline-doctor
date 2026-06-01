from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
import os
import pickle
from typing import Any

import mlflow
import mlflow.sklearn
from mlflow.models.signature import infer_signature
import pandas as pd
from pandas.api import types as ptypes
from sklearn.base import clone, is_classifier, is_regressor
from sklearn.metrics import accuracy_score, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sqlalchemy.orm import Session

from app.config import settings
from app.config.settings import MLFLOW_TRACKING_URI, resolve_mlflow_tracking_uri
from app.models.baseline import Baseline
from app.models.ml_model import MLModel
from app.models.pipeline_run import PipelineRun

IDENTIFIER_TOKENS = {"id", "uuid", "key"}
TARGET_NAME_HINTS = {
    "target",
    "label",
    "class",
    "outcome",
    "predictionlabel",
    "clusterlabel",
}


class RemediationCanceled(Exception):
    """Raised when a remediation run is canceled cooperatively."""


def collect_retraining_context(
    db: Session,
    pipeline_run: PipelineRun,
    model_record: MLModel,
) -> dict[str, Any]:
    expected_features, feature_source = resolve_expected_features(db, pipeline_run, model_record)
    cleaned_data_available = bool(
        pipeline_run.cleaned_data_path and os.path.exists(pipeline_run.cleaned_data_path)
    )
    dataset_columns: list[str] = []

    if cleaned_data_available:
        df = pd.read_csv(pipeline_run.cleaned_data_path, nrows=5)
        dataset_columns = [str(column) for column in df.columns]

    target_candidates = [
        column
        for column in dataset_columns
        if column not in expected_features and not _looks_like_identifier_column(column)
    ]

    readiness_warnings: list[str] = []
    if not cleaned_data_available:
        readiness_warnings.append(
            "Cleaned data is not available for this run, so retraining cannot start."
        )
    if not expected_features:
        readiness_warnings.append(
            "No feature list is configured for this model and no usable fallback could be derived from the active baseline."
        )
    elif feature_source == "baseline":
        readiness_warnings.append(
            "Expected features were inferred from the active baseline because the model record does not have an explicit feature list."
        )
    if cleaned_data_available and not target_candidates:
        readiness_warnings.append(
            "No target column candidates were found outside the resolved feature set."
        )

    return {
        "expected_features": expected_features,
        "expected_features_source": feature_source,
        "dataset_columns": dataset_columns,
        "target_candidates": target_candidates,
        "suggested_target_column": _suggest_target_column(target_candidates),
        "cleaned_data_available": cleaned_data_available,
        "readiness_warnings": readiness_warnings,
    }


def resolve_expected_features(
    db: Session,
    pipeline_run: PipelineRun,
    model_record: MLModel,
) -> tuple[list[str], str]:
    configured = _normalize_feature_list(model_record.expected_features)
    if configured:
        return configured, "model"

    baseline = _get_reference_baseline(db, pipeline_run)
    if not baseline:
        return [], "unavailable"

    inferred = _infer_features_from_baseline(baseline)
    if inferred:
        return inferred, "baseline"

    return [], "unavailable"


def prepare_retraining_plan(
    db: Session,
    pipeline_run: PipelineRun,
    model_record: MLModel,
    target_column: str,
) -> dict[str, Any]:
    if not pipeline_run.cleaned_data_path or not os.path.exists(pipeline_run.cleaned_data_path):
        raise ValueError("Cleaned data path is missing for retraining.")

    df = pd.read_csv(pipeline_run.cleaned_data_path)
    if df.empty:
        raise ValueError("Cleaned data is empty, so retraining cannot start.")

    expected_features, feature_source = resolve_expected_features(db, pipeline_run, model_record)
    if not expected_features:
        raise ValueError(
            "No expected feature list is configured for this model, and the active baseline could not provide a safe fallback."
        )

    if target_column not in df.columns:
        raise ValueError(
            f"Target column '{target_column}' was not found in cleaned data for run {pipeline_run.id}."
        )

    feature_columns = [
        column
        for column in expected_features
        if column in df.columns and column != target_column
    ]
    if not feature_columns:
        raise ValueError(
            "No configured feature columns are available in the cleaned dataset for retraining."
        )

    target_null_ratio = float(df[target_column].isna().mean())
    if target_null_ratio > settings.REMEDIATION_MAX_TARGET_NULL_RATIO:
        raise ValueError(
            f"Target column '{target_column}' has null ratio {target_null_ratio:.2f}, which exceeds the remediation threshold."
        )

    df = df.loc[df[target_column].notna(), :].copy()
    if len(df) < settings.REMEDIATION_MIN_TRAINING_ROWS:
        raise ValueError(
            f"At least {settings.REMEDIATION_MIN_TRAINING_ROWS} cleaned rows are required for retraining; only {len(df)} are available."
        )

    raw_target = df[target_column].copy()
    task_type = _infer_task_type(raw_target)
    target = _normalize_target_series(raw_target, task_type, target_column)
    df = df.loc[target.index].copy()

    features = _prepare_feature_frame(df, feature_columns)
    if features.empty:
        raise ValueError("Prepared training features are empty after normalization.")

    if len(features) < settings.REMEDIATION_MIN_TRAINING_ROWS:
        raise ValueError(
            f"Prepared training data fell below the minimum remediation row count of {settings.REMEDIATION_MIN_TRAINING_ROWS}."
        )

    split_kwargs = {
        "test_size": settings.REMEDIATION_TEST_SIZE,
        "random_state": 42,
    }
    class_distribution: dict[str, int] | None = None

    if task_type == "classification":
        class_distribution = {
            str(label): int(count)
            for label, count in target.value_counts(dropna=False).to_dict().items()
        }
        split_kwargs["stratify"] = target

    try:
        X_train, X_test, y_train, y_test = train_test_split(
            features,
            target,
            **split_kwargs,
        )
    except ValueError as exc:
        raise ValueError(f"Retraining split failed: {exc}") from exc

    return {
        "feature_columns": feature_columns,
        "feature_source": feature_source,
        "target_column": target_column,
        "task_type": task_type,
        "row_count": int(len(target)),
        "target_null_ratio": target_null_ratio,
        "class_distribution": class_distribution,
        "X_train": X_train,
        "X_test": X_test,
        "y_train": y_train,
        "y_test": y_test,
    }


def run_retraining(
    db: Session,
    run_id: int,
    model_id: int,
    target_column: str,
    should_cancel: Callable[[], bool] | None = None,
) -> dict[str, Any]:
    pipeline_run = db.query(PipelineRun).filter(PipelineRun.id == run_id).first()
    model_record = db.query(MLModel).filter(MLModel.id == model_id).first()

    if not pipeline_run:
        raise ValueError(f"Pipeline run {run_id} was not found.")
    if not model_record:
        raise ValueError(f"ML model {model_id} was not found.")

    plan = prepare_retraining_plan(
        db=db,
        pipeline_run=pipeline_run,
        model_record=model_record,
        target_column=target_column,
    )

    _raise_if_canceled(should_cancel, "Cancellation requested before model training started.")

    estimator, estimator_class, source_model_uri = _build_candidate_estimator(
        model_record=model_record,
        task_type=plan["task_type"],
    )

    estimator.fit(plan["X_train"], plan["y_train"])
    predictions = estimator.predict(plan["X_test"])
    metrics = _build_metrics(plan["task_type"], plan["y_test"], predictions)

    _raise_if_canceled(
        should_cancel,
        "Cancellation requested after model training completed but before candidate artifacts were recorded.",
    )

    artifact_dir = os.path.join("mlartifacts", "remediation")
    os.makedirs(artifact_dir, exist_ok=True)
    artifact_path = os.path.join(
        artifact_dir,
        f"model_{model_id}_run_{run_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.pkl",
    )
    with open(artifact_path, "wb") as file_handle:
        pickle.dump(estimator, file_handle)

    tracking_uri = resolve_mlflow_tracking_uri(model_record.mlflow_tracking_uri)
    mlflow.set_tracking_uri(tracking_uri or MLFLOW_TRACKING_URI)

    with mlflow.start_run(run_name=f"retraining_candidate_run_{run_id}") as active_run:
        mlflow.set_tags(
            {
                "remediation_candidate": "true",
                "source_model_id": str(model_id),
                "source_model_name": model_record.name,
                "source_model_version": str(model_record.version),
                "pipeline_run_id": str(run_id),
                "target_column": target_column,
                "feature_source": plan["feature_source"],
            }
        )
        mlflow.log_params(
            {
                "pipeline_run_id": run_id,
                "model_id": model_id,
                "target_column": target_column,
                "task_type": plan["task_type"],
                "feature_count": len(plan["feature_columns"]),
                "training_row_count": plan["row_count"],
            }
        )
        mlflow.log_metrics(metrics)
        signature = infer_signature(plan["X_train"], estimator.predict(plan["X_train"]))
        mlflow.sklearn.log_model(
            sk_model=estimator,
            artifact_path="candidate_model",
            signature=signature,
        )

        candidate_run_id = active_run.info.run_id
        candidate_model_uri = f"runs:/{candidate_run_id}/candidate_model"

    return {
        "task_type": plan["task_type"],
        "feature_columns": plan["feature_columns"],
        "feature_source": plan["feature_source"],
        "target_column": target_column,
        "row_count": plan["row_count"],
        "target_null_ratio": plan["target_null_ratio"],
        "class_distribution": plan["class_distribution"],
        "estimator_class": estimator_class,
        "metrics": metrics,
        "artifact_path": artifact_path,
        "candidate_mlflow_run_id": candidate_run_id,
        "candidate_model_uri": candidate_model_uri,
        "source_model_name": model_record.mlflow_model_name or model_record.name,
        "source_model_version": model_record.version,
        "source_model_uri": source_model_uri,
    }


def _get_reference_baseline(db: Session, pipeline_run: PipelineRun) -> Baseline | None:
    baseline = (
        db.query(Baseline)
        .filter(
            Baseline.model_id == pipeline_run.model_id,
            Baseline.version == pipeline_run.baseline_version,
        )
        .first()
    )
    if baseline:
        return baseline

    return (
        db.query(Baseline)
        .filter(Baseline.model_id == pipeline_run.model_id, Baseline.is_active.is_(True))
        .order_by(Baseline.version.desc())
        .first()
    )


def _infer_features_from_baseline(baseline: Baseline) -> list[str]:
    profile = baseline.profile or {}
    inferred: list[str] = []

    for column, rules in profile.items():
        if str(column).startswith("_"):
            continue

        if _looks_like_target_column(str(column)):
            continue

        rule_type = str((rules or {}).get("type") or "").lower()
        validation_mode = str((rules or {}).get("validation_mode") or "").lower()
        if rule_type in {"identifier", "text"} or validation_mode in {"identifier", "high_cardinality"}:
            continue

        inferred.append(str(column))

    if inferred:
        return inferred

    schema = baseline.schema or {}
    return [
        str(column)
        for column in schema.keys()
        if not _looks_like_identifier_column(str(column)) and not _looks_like_target_column(str(column))
    ]


def _normalize_feature_list(features: Any) -> list[str]:
    if not isinstance(features, list):
        return []

    normalized: list[str] = []
    for feature in features:
        feature_name = str(feature or "").strip()
        if feature_name and feature_name not in normalized:
            normalized.append(feature_name)

    return normalized


def _prepare_feature_frame(df: pd.DataFrame, feature_columns: list[str]) -> pd.DataFrame:
    features = df[feature_columns].copy()
    for column in feature_columns:
        if ptypes.is_bool_dtype(features[column]) or ptypes.is_numeric_dtype(features[column]):
            numeric_series = pd.to_numeric(features[column], errors="coerce")
            if numeric_series.notna().any():
                median_value = float(numeric_series.median())
                features[column] = numeric_series.fillna(median_value)
                continue

        features[column] = features[column].astype("string").fillna("UNKNOWN")

    encoded = pd.get_dummies(features, dummy_na=False)
    return encoded.fillna(0)


def _build_candidate_estimator(
    model_record: MLModel,
    task_type: str,
):
    if str(model_record.framework or "").lower() != "sklearn":
        raise ValueError(
            f"Remediation retraining currently supports only sklearn models. Found framework '{model_record.framework}'."
        )

    tracking_uri = resolve_mlflow_tracking_uri(model_record.mlflow_tracking_uri)
    mlflow.set_tracking_uri(tracking_uri or MLFLOW_TRACKING_URI)
    source_model_uri = _resolve_source_model_uri(model_record)

    try:
        source_estimator = mlflow.sklearn.load_model(source_model_uri)
    except Exception as exc:
        raise ValueError(
            f"Failed to load the source model from MLflow for remediation retraining: {exc}"
        ) from exc

    if task_type == "classification" and not is_classifier(source_estimator):
        raise ValueError(
            "The selected remediation target looks like a classification label, but the original model is not a classifier."
        )

    if task_type == "regression" and not is_regressor(source_estimator):
        raise ValueError(
            "The selected remediation target looks numeric/regression-oriented, but the original model is not a regressor."
        )

    try:
        estimator = clone(source_estimator)
    except Exception as exc:
        raise ValueError(
            f"Failed to clone the source sklearn estimator for retraining: {exc}"
        ) from exc

    return estimator, source_estimator.__class__.__name__, source_model_uri


def _resolve_source_model_uri(model_record: MLModel) -> str:
    if model_record.mlflow_run_id:
        return f"runs:/{model_record.mlflow_run_id}/model"

    if model_record.mlflow_model_name and model_record.version:
        return f"models:/{model_record.mlflow_model_name}/{model_record.version}"

    if model_record.mlflow_model_name and model_record.mlflow_alias:
        return f"models:/{model_record.mlflow_model_name}@{model_record.mlflow_alias}"

    raise ValueError(
        "The source model does not have enough MLflow metadata to load the original estimator for remediation retraining."
    )


def _infer_task_type(series: pd.Series) -> str:
    non_null = series.dropna()
    if non_null.empty:
        raise ValueError("Target column contains no usable values for retraining.")

    unique_count = int(non_null.nunique(dropna=True))
    unique_ratio = unique_count / max(len(non_null), 1)

    if ptypes.is_bool_dtype(non_null):
        return "classification"

    if ptypes.is_numeric_dtype(non_null):
        if unique_count < 2:
            raise ValueError("Target column must contain at least two distinct values for retraining.")
        if unique_count <= settings.REMEDIATION_MAX_CLASS_COUNT:
            return "classification"
        return "regression"

    if unique_count < 2:
        raise ValueError("Target column must contain at least two distinct values for retraining.")
    if unique_count > settings.REMEDIATION_MAX_CLASS_COUNT:
        raise ValueError(
            f"Target column has {unique_count} distinct values, which exceeds the remediation classification limit of {settings.REMEDIATION_MAX_CLASS_COUNT}."
        )
    if unique_ratio > settings.REMEDIATION_MAX_CLASS_UNIQUE_RATIO:
        raise ValueError(
            f"Target column has uniqueness ratio {unique_ratio:.2f}, which looks more like an identifier than a supervised label."
        )

    return "classification"


def _normalize_target_series(
    series: pd.Series,
    task_type: str,
    target_column: str,
) -> pd.Series:
    if task_type == "classification":
        normalized = series.astype("string").str.strip()
        counts = normalized.value_counts(dropna=False)
        if len(counts) < 2:
            raise ValueError("Target column must contain at least two classes for classification retraining.")
        if len(counts) > settings.REMEDIATION_MAX_CLASS_COUNT:
            raise ValueError(
                f"Target column has too many classes ({len(counts)}) for the current retraining policy."
            )
        if int(counts.min()) < settings.REMEDIATION_MIN_CLASS_COUNT:
            raise ValueError(
                f"Each class must have at least {settings.REMEDIATION_MIN_CLASS_COUNT} rows for safe retraining."
            )
        return normalized

    numeric_target = pd.to_numeric(series, errors="coerce")
    if numeric_target.isna().any():
        invalid_count = int(numeric_target.isna().sum())
        raise ValueError(
            f"Target column '{target_column}' contains {invalid_count} values that cannot be converted to numeric form for regression retraining."
        )
    if int(numeric_target.nunique(dropna=True)) < 2:
        raise ValueError("Regression retraining requires at least two distinct numeric target values.")
    return numeric_target


def _looks_like_identifier_column(column: str) -> bool:
    normalized = str(column).strip().lower().replace("_", "")
    return normalized in IDENTIFIER_TOKENS or normalized.endswith("id")


def _looks_like_target_column(column: str) -> bool:
    normalized = str(column).strip().lower().replace("_", "")
    return normalized in TARGET_NAME_HINTS


def _suggest_target_column(target_candidates: list[str]) -> str | None:
    if not target_candidates:
        return None

    preferred_names = [
        "target",
        "label",
        "class",
        "outcome",
        "prediction_label",
        "cluster_label",
    ]

    normalized_lookup = {
        column.lower(): column
        for column in target_candidates
    }

    for preferred in preferred_names:
        if preferred in normalized_lookup:
            return normalized_lookup[preferred]

    return target_candidates[0]


def _raise_if_canceled(
    should_cancel: Callable[[], bool] | None,
    message: str,
) -> None:
    if should_cancel and should_cancel():
        raise RemediationCanceled(message)


def _build_metrics(task_type: str, y_true, predictions) -> dict[str, float]:
    if task_type == "classification":
        return {
            "accuracy": float(accuracy_score(y_true, predictions)),
        }

    mse = float(mean_squared_error(y_true, predictions))
    return {
        "rmse": mse ** 0.5,
        "r2": float(r2_score(y_true, predictions)),
    }
