import pandas as pd
from typing import Dict, List, Any


class DataValidator:
    def __init__(self, df: pd.DataFrame, baseline: Dict[str, Any]):
        self.df = df
        self.schema = baseline["schema"]
        self.profile = baseline["profile"]

        self.schema_errors: List[str] = []
        self.checks: List[Dict[str, Any]] = []

    # -----------------------------
    # SCHEMA VALIDATION
    # -----------------------------
    def validate_schema(self):
        df_columns = set(self.df.columns)
        baseline_columns = set(self.schema.keys())

        missing = baseline_columns - df_columns
        extra = df_columns - baseline_columns

        if missing:
            self.schema_errors.append(f"Missing columns: {list(missing)}")

        if extra:
            self.schema_errors.append(f"Extra columns: {list(extra)}")

        # Type validation
        for col, expected_type in self.schema.items():
            if col in self.df.columns:
                actual_type = str(self.df[col].dtype)

                if actual_type != expected_type:
                    self.schema_errors.append(
                        f"Type mismatch in {col}: expected {expected_type}, got {actual_type}"
                    )

    # -----------------------------
    # NULL CHECKS
    # -----------------------------
    def validate_nulls(self, threshold: float = 0.3):
        for col in self.df.columns:
            null_ratio = self.df[col].isna().mean()

            success = null_ratio <= threshold

            self.checks.append({
                "column": col,
                "check": "null_ratio",
                "success": success,
                "details": f"null_ratio={null_ratio:.2f}, threshold={threshold}"
            })

    # -----------------------------
    # NUMERIC RANGE CHECKS
    # -----------------------------
    def validate_numeric_ranges(self):
        for col, rules in self.profile.items():
            if col not in self.df.columns:
                continue

            if "min" in rules and "max" in rules:
                series = self.df[col].dropna()

                if series.empty:
                    continue

                min_val = series.min()
                max_val = series.max()

                success = (min_val >= rules["min"]) and (max_val <= rules["max"])

                self.checks.append({
                    "column": col,
                    "check": "range",
                    "success": success,
                    "details": f"observed=({min_val},{max_val}), expected=({rules['min']},{rules['max']})"
                })

    # -----------------------------
    # CATEGORICAL CHECKS
    # -----------------------------
    def validate_categorical(self):
        for col, rules in self.profile.items():
            if col not in self.df.columns:
                continue

            if "allowed_values" in rules:
                observed = set(self.df[col].dropna().unique())
                allowed = set(rules["allowed_values"])

                unseen = observed - allowed

                success = len(unseen) == 0

                self.checks.append({
                    "column": col,
                    "check": "categorical",
                    "success": success,
                    "details": f"unseen_values={list(unseen)}"
                })

    # -----------------------------
    # RUN ALL
    # -----------------------------
    def run(self):
        self.validate_schema()

        # run checks on intersecting columns
        self.validate_nulls()
        self.validate_numeric()
        self.validate_categorical()

        failed = sum(1 for c in self.checks if not c["success"])

        return {
            "schema_errors": self.schema_errors,
            "checks": self.checks,
            "summary": {
                "total_checks": len(self.checks),
                "failed_checks": failed,
                "status": "FAIL" if self.schema_errors or failed else "PASS"
            }
        }