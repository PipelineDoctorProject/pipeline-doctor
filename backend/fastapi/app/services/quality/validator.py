import pandas as pd
from typing import Any, Dict, List

from app.config import settings
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
        return normalized in IDENTIFIER_TOKENS or normalized.endswith("id")

    def _should_validate_categorical(self, col: str, rules: Dict[str, Any]) -> bool:
        if self._is_identifier_column(col):
            return False

        validation_mode = rules.get("validation_mode")
        if validation_mode in {"identifier", "high_cardinality", "text"}:
            return False

        allowed_values = rules.get("unique_values") or []
        if not allowed_values:
            return False

        non_null = self.df[col].dropna()
        if non_null.empty:
            return False

        unique_count = int(non_null.astype(str).str.strip().nunique())
        row_count = int(len(non_null))

        if len(allowed_values) >= settings.DATA_QUALITY_CATEGORICAL_LIMIT:
            if unique_count >= settings.DATA_QUALITY_HIGH_CARDINALITY_LIMIT:
                return False
            if (unique_count / max(row_count, 1)) >= settings.DATA_QUALITY_HIGH_CARDINALITY_RATIO:
                return False

        return True

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

    def validate_nulls(self, threshold: float = settings.DATA_QUALITY_NULL_RATIO_THRESHOLD):
        for col in self.schema.keys():
            if col not in self.df.columns:
                continue

            row_count = int(len(self.df))
            ratio = float(self.df[col].isna().mean()) if row_count else 1.0

            self.checks.append(
                {
                    "column": col,
                    "check": "null_ratio",
                    "success": bool(ratio <= threshold),
                    "details": f"{ratio:.2f} (threshold={threshold})",
                    "metadata": {
                        "ratio": ratio,
                        "threshold": threshold,
                        "missing_count": int(self.df[col].isna().sum()),
                        "row_count": row_count,
                    },
                }
            )

    def validate_numeric_ranges(self):
        for col, rules in self.profile.items():
            if col.startswith("_"):
                continue

            if col not in self.df.columns:
                continue

            if self._is_identifier_column(col):
                continue

            if "min" in rules and "max" in rules:
                baseline_min = float(rules.get("p01", rules["min"]))
                baseline_max = float(rules.get("p99", rules["max"]))

                series = pd.to_numeric(self.df[col], errors="coerce").dropna()
                if series.empty:
                    continue

                min_val = float(series.min())
                max_val = float(series.max())
                success = min_val >= baseline_min and max_val <= baseline_max

                self.checks.append(
                    {
                        "column": col,
                        "check": "range",
                        "success": bool(success),
                        "details": f"{min_val}-{max_val} vs {baseline_min}-{baseline_max}",
                        "metadata": {
                            "observed_min": min_val,
                            "observed_max": max_val,
                            "baseline_min": baseline_min,
                            "baseline_max": baseline_max,
                            "below_min_count": int((series < baseline_min).sum()),
                            "above_max_count": int((series > baseline_max).sum()),
                        },
                    }
                )

    def validate_categorical(self):
        for col, rules in self.profile.items():
            if col.startswith("_"):
                continue

            if col not in self.df.columns:
                continue

            if not self._should_validate_categorical(col, rules):
                continue

            observed = set(
                self.df[col]
                .dropna()
                .astype(str)
                .str.strip()
                .str.upper()
                .unique()
            )
            allowed = set(str(value).strip().upper() for value in rules["unique_values"])
            unseen = observed - allowed

            self.checks.append(
                {
                    "column": col,
                    "check": "categorical",
                    "success": bool(len(unseen) == 0),
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
                }
            )

    def run(self):
        self.validate_schema()
        self.validate_nulls()
        self.validate_numeric_ranges()
        self.validate_categorical()

        failed = int(sum(1 for check in self.checks if not check["success"]))
        total_checks = int(len(self.checks))

        return {
            "schema_errors": self.schema_errors,
            "checks": self.checks,
            "summary": {
                "total_checks": total_checks,
                "failed_checks": failed,
                "failed_check_ratio": float(failed / total_checks) if total_checks else 0.0,
                "status": "FAIL" if self.schema_errors or failed else "PASS",
            },
        }
