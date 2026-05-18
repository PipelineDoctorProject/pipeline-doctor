import pandas as pd
from typing import Dict, List, Any
from app.services.quality.type_utils import normalize_dtype

MISSING_MARKERS = {"", "NA", "N/A", "NULL", "NONE", "NAN"}
IDENTIFIER_TOKENS = {"id", "uuid", "key"}

class DataValidator:
    def __init__(self, df: pd.DataFrame, baseline: Dict[str, Any]):
        self.df = self._normalize_missing_markers(df.copy())
        self.schema = baseline["schema"]
        self.profile = baseline["profile"]

        self.schema_errors: List[str] = []
        self.checks: List[Dict[str, Any]] = []

    def _normalize_missing_markers(self, df: pd.DataFrame) -> pd.DataFrame:
        object_cols = df.select_dtypes(include=["object"]).columns

        for col in object_cols:
            stripped = df[col].astype("string").str.strip()
            df[col] = df[col].mask(stripped.str.upper().isin(MISSING_MARKERS))

        return df

    def _non_null_values(self, col: str) -> pd.Series:
        return self.df[col].dropna()

    def _numeric_values(self, values: pd.Series) -> pd.Series:
        return pd.to_numeric(values, errors="coerce")

    def _has_invalid_numeric_values(self, values: pd.Series) -> bool:
        if values.empty:
            return False

        numeric = self._numeric_values(values)
        return bool(numeric.isna().any())

    def _is_int_like(self, values: pd.Series) -> bool:
        if values.empty:
            return True

        numeric = self._numeric_values(values)

        if numeric.isna().any():
            return False

        return bool((numeric % 1 == 0).all())

    def _is_type_compatible(self, col: str, expected_type: str, actual_type: str) -> bool:
        values = self._non_null_values(col)

        if actual_type == expected_type:
            return True

        # CSV blanks can make integer columns read as float64 because NaN is a
        # float value. Accept those columns when every present value is whole.
        if expected_type == "int":
            return actual_type in ["float", "object"] and self._is_int_like(values)

        if expected_type == "float":
            if actual_type == "int":
                return True

            if actual_type == "object":
                return not self._has_invalid_numeric_values(values)

        return False

    def _is_identifier_column(self, col: str) -> bool:
        normalized = col.strip().lower().replace("_", "")

        if normalized in IDENTIFIER_TOKENS or normalized.endswith("id"):
            return True

        return False

    # -----------------------------
    # TYPE VALIDATION
    # -----------------------------
    def validate_schema(self):

        for col, expected_type in self.schema.items():

            if col not in self.df.columns:
                continue

            actual_type = normalize_dtype(self.df[col].dtype)
            expected_type = normalize_dtype(expected_type)

            if not self._is_type_compatible(col, expected_type, actual_type):

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
                "details": f"{ratio:.2f} (threshold={threshold})",
                "metadata": {
                    "ratio": ratio,
                    "threshold": threshold,
                    "missing_count": int(self.df[col].isna().sum()),
                    "row_count": int(len(self.df)),
                },
            })

    # -----------------------------
    # NUMERIC RANGE
    # -----------------------------
    def validate_numeric_ranges(self):

        for col, rules in self.profile.items():

            if col not in self.df.columns:
                continue

            if self._is_identifier_column(col):
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
                    "details": f"{min_val}-{max_val} vs {rules['min']}-{rules['max']}",
                    "metadata": {
                        "observed_min": min_val,
                        "observed_max": max_val,
                        "baseline_min": float(rules["min"]),
                        "baseline_max": float(rules["max"]),
                        "below_min_count": int((series < rules["min"]).sum()),
                        "above_max_count": int((series > rules["max"]).sum()),
                    },
                })

    # -----------------------------
    # CATEGORICAL
    # -----------------------------
    def validate_categorical(self):
        for col, rules in self.profile.items():
            if col not in self.df.columns:
                continue

            if "unique_values" in rules:
                observed = set(
                    self.df[col]
                    .dropna()
                    .astype(str)
                    .str.strip()
                    .str.upper()
                    .unique()
                )
                allowed = set(
                    str(value).strip().upper()
                    for value in rules["unique_values"]
                )

                unseen = observed - allowed

                self.checks.append({
                    "column": col,
                    "check": "categorical",
                    "success": bool(len(unseen) == 0),  # 🔥 FIX
                    "details": f"unseen={sorted(unseen)}",
                    "metadata": {
                        "unseen_values": sorted(unseen),
                        "allowed_values_sample": sorted(allowed)[:20],
                        "unseen_count": int(
                            self.df[col]
                            .dropna()
                            .astype(str)
                            .str.strip()
                            .str.upper()
                            .isin(unseen)
                            .sum()
                        ),
                    },
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
