import pandas as pd

from app.services.quality.type_utils import normalize_dtype


def classify_column(series: pd.Series):

    dtype = normalize_dtype(series.dtype)

    # numeric
    if dtype in ["int", "float"]:
        return "numeric"

    # boolean
    if dtype == "bool":
        return "boolean"

    # datetime
    if dtype == "datetime":
        return "datetime"

    # default
    return "categorical"