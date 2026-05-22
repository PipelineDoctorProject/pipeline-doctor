import pandas as pd
import os


def load_dataset(file_path: str):

    ext = os.path.splitext(file_path)[1].lower()

    # CSV
    if ext == ".csv":
        return pd.read_csv(file_path)

    # PARQUET
    elif ext == ".parquet":
        return pd.read_parquet(file_path)

    # JSON
    elif ext == ".json":
        return pd.read_json(file_path)

    else:
        raise Exception(f"Unsupported file type: {ext}")