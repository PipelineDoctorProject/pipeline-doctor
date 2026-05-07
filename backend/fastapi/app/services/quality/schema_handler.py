import pandas as pd
from typing import Tuple, List, Dict


def handle_schema(df: pd.DataFrame, baseline_schema: Dict):
    expected_cols = set(baseline_schema.keys())
    incoming_cols = set(df.columns)

    extra_cols = list(incoming_cols - expected_cols)
    missing_cols = list(expected_cols - incoming_cols)

    # 🔹 Drop extra columns (safe contract enforcement)
    df_aligned = df.drop(columns=extra_cols, errors="ignore")

    # 🔹 Add missing columns as NULL
    for col in missing_cols:
        df_aligned[col] = None

    # 🔹 Reorder columns
    df_aligned = df_aligned[list(baseline_schema.keys())]

    return df_aligned, extra_cols, missing_cols