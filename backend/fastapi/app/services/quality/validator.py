import pandas as pd
from typing import Dict, List, Any
from app.services.quality.type_utils import normalize_dtype

class DataValidator:
    def __init__(self, df: pd.DataFrame, baseline: Dict[str, Any]):
        self.df = df
        self.schema = baseline["schema"]
        self.profile = baseline["profile"]

        self.schema_errors: List[str] = []
        self.checks: List[Dict[str, Any]] = []

    # -----------------------------
    # TYPE VALIDATION
    # -----------------------------
    def validate_schema(self):

        for col, expected_type in self.schema.items():

            if col not in self.df.columns:
                continue

            actual_type = normalize_dtype(self.df[col].dtype)
            expected_type = normalize_dtype(expected_type)

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

            ratio = float(self.df[col].isna().mean())  #  FIX

            self.checks.append({
                "column": col,
                "check": "null_ratio",
                "success": bool(ratio <= threshold),  #  FIX
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

                # SAFE numeric conversion
                series = pd.to_numeric(
                    self.df[col],
                    errors="coerce"
                ).dropna()

                if series.empty:
                    continue

                min_val = float(series.min())
                max_val = float(series.max())

                success = (
                    min_val >= rules["min"]
                    and max_val <= rules["max"]
                )

                self.checks.append({
                    "column": col,
                    "check": "range",
                    "success": bool(success),
                    "details": f"{min_val}-{max_val} vs {rules['min']}-{rules['max']}"
                })

    # -----------------------------
    # CATEGORICAL
    # -----------------------------
    def validate_categorical(self):
        for col, rules in self.profile.items():
            if col not in self.df.columns:
                continue

            if "unique_values" in rules:
                observed = set(self.df[col].dropna().astype(str).unique())
                allowed = set(map(str, rules["unique_values"]))

                unseen = observed - allowed

                self.checks.append({
                    "column": col,
                    "check": "categorical",
                    "success": bool(len(unseen) == 0),  # 🔥 FIX
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

        failed = int(sum(1 for c in self.checks if not c["success"]))  # 🔥 FIX

        return {
            "schema_errors": self.schema_errors,
            "checks": self.checks,
            "summary": {
                "total_checks": int(len(self.checks)),  # 🔥 FIX
                "failed_checks": failed,
                "status": "FAIL" if self.schema_errors or failed else "PASS"
            }
        }