import argparse
import os
from pathlib import Path

import mlflow
import mlflow.sklearn
import pandas as pd
from mlflow.models.signature import infer_signature
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


DEFAULT_FEATURE_COLUMNS = [
    "danceability",
    "energy",
    "key",
    "loudness",
    "mode",
    "speechiness",
    "acousticness",
    "instrumentalness",
    "liveness",
    "valence",
    "tempo",
    "duration_ms",
    "time_signature",
]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Register the local source KMeans model used by OpsSight remediation."
    )
    parser.add_argument(
        "--data-path",
        required=True,
        help="CSV path to trusted baseline/source data.",
    )
    parser.add_argument(
        "--model-name",
        default="spotify-kmeans-recommender",
        help="Registered model name expected by OpsSight.",
    )
    parser.add_argument(
        "--experiment-name",
        default="OpsSight Local Source Models",
        help="MLflow experiment name.",
    )
    parser.add_argument(
        "--tracking-uri",
        default=os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000"),
        help="MLflow tracking URI. Use http://mlflow:5000 inside Docker.",
    )
    parser.add_argument(
        "--feature",
        action="append",
        dest="features",
        help="Feature column to use. Repeat this flag to override defaults.",
    )
    parser.add_argument(
        "--n-clusters",
        type=int,
        default=5,
        help="Number of KMeans clusters.",
    )
    return parser.parse_args()


def _load_features(data_path: Path, requested_features: list[str] | None) -> pd.DataFrame:
    if not data_path.exists():
        raise FileNotFoundError(f"CSV file not found: {data_path}")

    df = pd.read_csv(data_path)
    feature_columns = requested_features or DEFAULT_FEATURE_COLUMNS
    missing = [column for column in feature_columns if column not in df.columns]
    if missing:
        raise ValueError(f"Missing feature column(s) in CSV: {missing}")

    features = df[feature_columns].copy()
    if features.empty:
        raise ValueError("No rows available for model bootstrap.")
    return features


def _build_pipeline(features: pd.DataFrame, n_clusters: int) -> Pipeline:
    numeric_columns = [
        column
        for column in features.columns
        if pd.to_numeric(features[column], errors="coerce").notna().any()
    ]
    categorical_columns = [
        column
        for column in features.columns
        if column not in numeric_columns
    ]

    for column in numeric_columns:
        features[column] = pd.to_numeric(features[column], errors="coerce")
        features[column] = features[column].fillna(float(features[column].median()))

    for column in categorical_columns:
        features[column] = features[column].astype("string").fillna("UNKNOWN")

    transformers = []
    if numeric_columns:
        transformers.append(("numeric", StandardScaler(), numeric_columns))
    if categorical_columns:
        transformers.append(
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore"),
                categorical_columns,
            )
        )

    if not transformers:
        raise ValueError("No usable numeric or categorical features were found.")

    return Pipeline(
        steps=[
            ("preprocess", ColumnTransformer(transformers=transformers)),
            ("cluster", KMeans(n_clusters=n_clusters, random_state=42, n_init="auto")),
        ]
    )


def main() -> None:
    args = _parse_args()
    data_path = Path(args.data_path)
    features = _load_features(data_path, args.features)
    pipeline = _build_pipeline(features, args.n_clusters)

    mlflow.set_tracking_uri(args.tracking_uri)
    mlflow.set_experiment(args.experiment_name)

    with mlflow.start_run(run_name=f"bootstrap-{args.model_name}") as run:
        pipeline.fit(features)
        predictions = pipeline.predict(features)
        signature = infer_signature(features, predictions)

        mlflow.log_param("model_type", "KMeans")
        mlflow.log_param("training_mode", "unsupervised_clustering")
        mlflow.log_param("n_clusters", args.n_clusters)
        mlflow.log_param("source_data_path", str(data_path))
        mlflow.log_param("feature_columns", ",".join(features.columns))
        mlflow.log_metric("inertia", float(pipeline.named_steps["cluster"].inertia_))
        mlflow.set_tags(
            {
                "project": "OpsSight",
                "environment": "local-development",
                "purpose": "source-model-bootstrap",
            }
        )

        mlflow.sklearn.log_model(
            sk_model=pipeline,
            artifact_path="model",
            registered_model_name=args.model_name,
            input_example=features.head(2),
            signature=signature,
        )

        from mlflow import MlflowClient
        client = MlflowClient(tracking_uri=args.tracking_uri)
        latest_versions = client.get_latest_versions(args.model_name)
        if latest_versions:
            latest_version = latest_versions[0].version
            client.set_registered_model_alias(
                name=args.model_name,
                alias="champion",
                version=latest_version
            )
            print(f"Assigned alias 'champion' to version {latest_version} of registered model '{args.model_name}'")

        print("Registered local MLflow model successfully.")
        print(f"model_name={args.model_name}")
        print(f"tracking_uri={args.tracking_uri}")
        print(f"run_id={run.info.run_id}")
        print(f"feature_columns={list(features.columns)}")


if __name__ == "__main__":
    main()
