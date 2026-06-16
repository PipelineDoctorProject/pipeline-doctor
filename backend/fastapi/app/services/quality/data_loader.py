import pandas as pd
import os

from app.services import file_storage


def load_dataset(file_path: str):

    ext = os.path.splitext(file_path)[1].lower()

    # CSV
    if ext == ".csv":
        if file_storage.is_blob_uri(file_path):
            return pd.read_csv(file_storage.open_binary(file_path))
        return pd.read_csv(file_path)

    # PARQUET
    elif ext == ".parquet":
        return pd.read_parquet(file_path)

    # JSON
    elif ext == ".json":
        return pd.read_json(file_path)

    else:
        raise Exception(f"Unsupported file type: {ext}")
