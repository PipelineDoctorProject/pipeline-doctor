import pandas as pd
from typing import Tuple, List, Dict


def handle_schema(df: pd.DataFrame, baseline_schema: Dict):
    expected_cols = set(baseline_schema.keys())
    incoming_cols = set(df.columns)

    extra_cols = list(incoming_cols - expected_cols)
    missing_cols = list(expected_cols - incoming_cols)

    # Drop extra
    df = df.drop(columns=extra_cols, errors="ignore")

    # Add missing
    for col in missing_cols:
        df[col] = None

    # Reorder
    df = df[list(baseline_schema.keys())]

    return df, extra_cols, missing_cols