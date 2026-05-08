import pandas as pd


def normalize_dtype(dtype: str):
    if "int" in dtype:
        return "int"
    elif "float" in dtype:
        return "float"
    else:
        return "object"


def extract_schema(df: pd.DataFrame):
    return {col: normalize_dtype(str(df[col].dtype)) for col in df.columns}


def build_profile(df: pd.DataFrame):
    profile = {}

    for col in df.columns:

        if pd.api.types.is_numeric_dtype(df[col]):
            series = df[col].dropna()

            if series.empty:
                continue

            profile[col] = {
                "type": "numeric",
                "min": float(series.min()),
                "max": float(series.max()),
                "mean": float(series.mean())
            }

        else:
            unique_vals = df[col].dropna().unique()

            profile[col] = {
                "type": "categorical",
                "unique_values": unique_vals[:50].tolist()  # limit size
            }

    return profile


def create_baseline(df: pd.DataFrame):
    return {
        "schema": extract_schema(df),
        "profile": build_profile(df)
    }