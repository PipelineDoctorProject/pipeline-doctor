from __future__ import annotations

from datetime import datetime
import os
import pickle
from typing import Any

import mlflow
import mlflow.sklearn
from mlflow.models.signature import infer_signature
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sqlalchemy.orm import Session

from app.config.settings import MLFLOW_TRACKING_URI, resolve_mlflow_tracking_uri
from app.models.ml_model import MLModel
from app.models.pipeline_run import PipelineRun


def run_retraining(
    db: Session,
    run_id: int,
    model_id: int,
    target_column: str,
) -> dict[str, Any]:
    pipeline_run = db.query(PipelineRun).filter(PipelineRun.id == run_id).first()
    model_record = db.query(MLModel).filter(MLModel.id == model_id).first()

    if not pipeline_run:
        raise ValueError(f"Pipeline run {run_id} was not found.")
    if not model_record:
        raise ValueError(f"ML model {model_id} was not found.")
    if not pipeline_run.cleaned_data_path or not os.path.exists(pipeline_run.cleaned_data_path):
        raise ValueError("Cleaned data path is missing for retraining.")

    df = pd.read_csv(pipeline_run.cleaned_data_path)
    if target_column not in df.columns:
        raise ValueError(
            f"Target column '{target_column}' was not found in cleaned data for run {run_id}."
        )

    if not model_record.expected_features:
        raise ValueError(
            "Model expected_features is empty. Configure the model feature list before approving retraining."
        )

    feature_columns = [
        column
        for column in model_record.expected_features
        if column in df.columns and column != target_column
    ]

    if not feature_columns:
        raise ValueError(
            "No configured feature columns are available in the cleaned dataset for retraining."
        )

    X = df[feature_columns].copy()
    y = df[target_column].copy()

    X = pd.get_dummies(X).fillna(0)
    task_type = "classification" if _is_classification_target(y) else "regression"
    estimator = (
        RandomForestClassifier(n_estimators=100, random_state=42)
        if task_type == "classification"
        else RandomForestRegressor(n_estimators=100, random_state=42)
    )

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
    )

    estimator.fit(X_train, y_train)
    predictions = estimator.predict(X_test)
    metrics = _build_metrics(task_type, y_test, predictions)

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

    with mlflow.start_run(run_name=f"retraining_run_{run_id}") as active_run:
        mlflow.log_params(
            {
                "pipeline_run_id": run_id,
                "model_id": model_id,
                "target_column": target_column,
                "task_type": task_type,
            }
        )
        mlflow.log_metrics(metrics)
        signature = infer_signature(X_train, estimator.predict(X_train))
        mlflow.sklearn.log_model(
            sk_model=estimator,
            artifact_path="model",
            registered_model_name=model_record.mlflow_model_name or None,
            signature=signature,
        )

        model_record.mlflow_run_id = active_run.info.run_id
        db.commit()

    return {
        "task_type": task_type,
        "feature_columns": feature_columns,
        "target_column": target_column,
        "metrics": metrics,
        "artifact_path": artifact_path,
        "mlflow_run_id": model_record.mlflow_run_id,
        "registered_model_name": model_record.mlflow_model_name,
    }


def _is_classification_target(series: pd.Series) -> bool:
    if series.dtype == object:
        return True
    unique_count = series.nunique(dropna=True)
    return unique_count <= 20


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
