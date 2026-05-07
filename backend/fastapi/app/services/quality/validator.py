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
    # TYPE VALIDATION ONLY
    # -----------------------------
    def validate_schema(self):
        for col, expected_type in self.schema.items():
            if col in self.df.columns:
                actual_type = str(self.df[col].dtype)

                if actual_type != expected_type:
                    self.schema_errors.append(
                        f"{col}: expected {expected_type}, got {actual_type}"
                    )

    # -----------------------------
    # NULL CHECK
    # -----------------------------
    def validate_nulls(self, threshold: float = 0.3):
        for col in self.schema.keys():
            if col not in self.df.columns:
                continue

            ratio = self.df[col].isna().mean()

            self.checks.append({
                "column": col,
                "check": "null_ratio",
                "success": ratio <= threshold,
                "details": f"{ratio:.2f} (threshold={threshold})"
            })

    # -----------------------------
    # NUMERIC RANGE
    # -----------------------------
    def validate_numeric_ranges(self):
        for col, rules in self.profile.items():
            if col not in self.df.columns:
                continue

            if "min" in rules and "max" in rules:
                series = self.df[col].dropna()
                if series.empty:
                    continue

                success = (
                    series.min() >= rules["min"]
                    and series.max() <= rules["max"]
                )

                self.checks.append({
                    "column": col,
                    "check": "range",
                    "success": success,
                    "details": f"{series.min()}-{series.max()} vs {rules['min']}-{rules['max']}"
                })

    # -----------------------------
    # CATEGORICAL
    # -----------------------------
    def validate_categorical(self):
        for col, rules in self.profile.items():
            if col not in self.df.columns:
                continue

            if "unique_values" in rules:
                observed = set(self.df[col].dropna().unique())
                allowed = set(rules["unique_values"])

                unseen = observed - allowed

                self.checks.append({
                    "column": col,
                    "check": "categorical",
                    "success": len(unseen) == 0,
                    "details": f"unseen={list(unseen)}"
                })

    # -----------------------------
    # RUN
    # -----------------------------
    def run(self):
        self.validate_schema()
        self.validate_nulls()
        self.validate_numeric_ranges()
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