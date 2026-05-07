import pandas as pd


def extract_schema(df: pd.DataFrame):
    return {col: str(df[col].dtype) for col in df.columns}


def build_profile(df: pd.DataFrame):
    profile = {}
    print(df)
    for col in df.columns:

        if pd.api.types.is_numeric_dtype(df[col]):
            profile[col] = {
                "type": "numeric",
                "min": float(df[col].min()),
                "max": float(df[col].max()),
                "mean": float(df[col].mean())
            }

        else:
            profile[col] = {
                "type": "categorical",
                "unique_values": df[col].dropna().unique().tolist()
            }

    return profile


def create_baseline(df: pd.DataFrame):
    return {
        "schema": extract_schema(df),
        "profile": build_profile(df)
    }


# You convert raw CSV → validation rules
# CSV → schema + profile → used for real-time checks