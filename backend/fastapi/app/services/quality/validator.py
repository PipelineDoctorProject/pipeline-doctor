def run_validation(df, baseline):

    results = {
        "schema_errors": [],
        "checks": []
    }

    # 1. SCHEMA CHECK
    for col in baseline["schema"]:

        if col not in df.columns:
            results["schema_errors"].append({
                "column": col,
                "error": "missing_column"
            })

        elif str(df[col].dtype) != baseline["schema"][col]:
            results["schema_errors"].append({
                "column": col,
                "error": "type_mismatch"
            })

    # 2. NULL CHECK
    for col in df.columns:
        has_null = df[col].isnull().any()

        results["checks"].append({
            "column": col,
            "check": "not_null",
            "success": not has_null
        })

    # 3. RANGE CHECK
    for col, stats in baseline["profile"].items():

        if stats["type"] == "numeric":

            out_of_range = (
                (df[col] < stats["min"]) |
                (df[col] > stats["max"])
            ).any()

            results["checks"].append({
                "column": col,
                "check": "range",
                "success": not out_of_range
            })

    # 4. CATEGORY CHECK
    for col, stats in baseline["profile"].items():

        if stats["type"] == "categorical":

            invalid = ~df[col].isin(stats["unique_values"])

            results["checks"].append({
                "column": col,
                "check": "category",
                "success": not invalid.any()
            })

    return results