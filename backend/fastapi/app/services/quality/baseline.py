import pandas as pd
from app.services.quality.type_utils import normalize_dtype

from app.services.quality.column_classifier import classify_column

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
                "mean": float(series.mean())
            }

        # -------------------------
        # CATEGORICAL
        # -------------------------
        else:

            unique_vals = (
                df[col]
                .dropna()
                .astype(str)
                .unique()
            )

            profile[col] = {
                "type": "categorical",
                "unique_values": unique_vals[:50].tolist()
            }

    return profile


def create_baseline(df: pd.DataFrame):
    return {
        "schema": extract_schema(df),
        "profile": build_profile(df)
    }