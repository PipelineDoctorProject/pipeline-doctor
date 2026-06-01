import pandas as pd
from app.services.quality.type_utils import normalize_dtype

from app.services.quality.column_classifier import classify_column
from app.config import settings

IDENTIFIER_TOKENS = {"id", "uuid", "key"}


def _is_identifier_column(col: str) -> bool:
    normalized = str(col).strip().lower().replace("_", "")
    return normalized in IDENTIFIER_TOKENS or normalized.endswith("id")


def _is_high_cardinality(series: pd.Series) -> bool:
    non_null = series.dropna()
    if non_null.empty:
        return False

    unique_count = int(non_null.astype(str).nunique())
    row_count = int(len(non_null))
    if unique_count >= settings.DATA_QUALITY_HIGH_CARDINALITY_LIMIT:
        return True

    return (unique_count / max(row_count, 1)) >= settings.DATA_QUALITY_HIGH_CARDINALITY_RATIO

def extract_schema(df: pd.DataFrame):

    schema = {}

    for col in df.columns:
        schema[col] = normalize_dtype(df[col].dtype)

    return schema

def build_profile(df: pd.DataFrame):

    profile = {}

    for col in df.columns:

        col_type = classify_column(df[col])

        # -------------------------
        # NUMERIC
        # -------------------------
        if col_type == "numeric":

            series = pd.to_numeric(
                df[col],
                errors="coerce"
            ).dropna()

            if series.empty:
                continue

            profile[col] = {
                "type": "numeric",
                "min": float(series.min()),
                "max": float(series.max()),
                "mean": float(series.mean()),
                "median": float(series.median()),
                "p01": float(series.quantile(0.01)),
                "p99": float(series.quantile(0.99)),
            }

        # -------------------------
        # CATEGORICAL
        # -------------------------
        else:
            if _is_identifier_column(col):
                profile[col] = {
                    "type": "identifier",
                    "validation_mode": "identifier",
                }
                continue

            if _is_high_cardinality(df[col]):
                unique_vals = (
                    df[col]
                    .dropna()
                    .astype(str)
                    .unique()
                )
                profile[col] = {
                    "type": "text",
                    "validation_mode": "high_cardinality",
                    "sample_values": unique_vals[:20].tolist(),
                }
                continue

            unique_vals = (
                df[col]
                .dropna()
                .astype(str)
                .unique()
            )

            profile[col] = {
                "type": "categorical",
                "validation_mode": "enum",
                "unique_values": unique_vals[: settings.DATA_QUALITY_CATEGORICAL_LIMIT].tolist()
            }

    return profile


def create_baseline(df: pd.DataFrame):
    return {
        "schema": extract_schema(df),
        "profile": build_profile(df)
    }
