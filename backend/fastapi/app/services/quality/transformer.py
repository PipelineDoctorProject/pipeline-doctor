import pandas as pd
from typing import Any, Dict

from app.config import settings

MISSING_MARKERS = {"", "NA", "N/A", "NULL", "NONE", "NAN"}
IDENTIFIER_TOKENS = {"id", "uuid", "key"}
BOOLEAN_TRUE_VALUES = {"true", "1", "yes", "y", "t"}
BOOLEAN_FALSE_VALUES = {"false", "0", "no", "n", "f"}


class DataTransformer:
    def __init__(self, df: pd.DataFrame, schema: dict, profile: Dict[str, Any] | None = None):
        self.df = df.copy()
        self.schema = schema
        self.profile = profile or {}
        self.issue_counts = pd.Series(0, index=self.df.index, dtype="int64")
        self.removed_rows = pd.DataFrame(columns=self.df.columns)
        self.audit = {
            "rows_in": int(len(self.df)),
            "rows_out": int(len(self.df)),
            "rows_removed": 0,
            "row_issue_threshold": settings.DATA_QUALITY_ROW_ISSUE_THRESHOLD,
            "column_issue_counts": {},
        }

    def _record_issue(self, mask: pd.Series, column: str):
        if mask is None or not bool(mask.any()):
            return

        aligned_mask = mask.reindex(self.df.index, fill_value=False)
        self.issue_counts = self.issue_counts.add(aligned_mask.astype("int64"), fill_value=0)
        self.audit["column_issue_counts"][column] = (
            int(self.audit["column_issue_counts"].get(column, 0)) + int(aligned_mask.sum())
        )

    def _is_identifier_column(self, col: str) -> bool:
        normalized = col.strip().lower().replace("_", "")
        return normalized in IDENTIFIER_TOKENS or normalized.endswith("id")

    def _is_enum_column(self, col: str, rules: Dict[str, Any]) -> bool:
        if self._is_identifier_column(col):
            return False

        validation_mode = rules.get("validation_mode")
        if validation_mode in {"identifier", "high_cardinality", "text"}:
            return False

        return bool(rules.get("unique_values"))

    def normalize_missing_markers(self):
        object_cols = self.df.select_dtypes(include=["object"]).columns

        for col in object_cols:
            stripped = self.df[col].astype("string").str.strip()
            missing_mask = self.df[col].notna() & stripped.str.upper().isin(MISSING_MARKERS)
            self._record_issue(missing_mask, col)
            self.df[col] = self.df[col].mask(missing_mask)

    def sanitize_numeric_columns(self):
        for col, dtype in self.schema.items():
            if col not in self.df.columns or dtype not in {"int", "float"}:
                continue

            original = self.df[col]
            coerced = pd.to_numeric(original, errors="coerce")
            invalid_mask = original.notna() & coerced.isna()
            self._record_issue(invalid_mask, col)

            rules = self.profile.get(col, {})
            if not self._is_identifier_column(col) and "min" in rules and "max" in rules:
                baseline_min = float(rules.get("p01", rules["min"]))
                baseline_max = float(rules.get("p99", rules["max"]))
                out_of_range_mask = coerced.notna() & (
                    (coerced < baseline_min) | (coerced > baseline_max)
                )
                self._record_issue(out_of_range_mask, col)
                coerced = coerced.mask(out_of_range_mask)

            self.df[col] = coerced

    def sanitize_boolean_columns(self):
        for col, dtype in self.schema.items():
            if col not in self.df.columns or dtype != "bool":
                continue

            normalized = self.df[col].astype("string").str.strip().str.lower()
            true_mask = normalized.isin(BOOLEAN_TRUE_VALUES)
            false_mask = normalized.isin(BOOLEAN_FALSE_VALUES)
            valid_mask = true_mask | false_mask | normalized.isna()
            invalid_mask = self.df[col].notna() & ~valid_mask
            self._record_issue(invalid_mask, col)

            mapped = pd.Series(pd.NA, index=self.df.index, dtype="boolean")
            mapped.loc[true_mask] = True
            mapped.loc[false_mask] = False
            self.df[col] = mapped

    def sanitize_categoricals(self):
        for col, dtype in self.schema.items():
            if col not in self.df.columns or dtype in {"int", "float", "bool"}:
                continue

            rules = self.profile.get(col, {})
            normalized = self.df[col].astype("string").str.strip()

            if self._is_enum_column(col, rules):
                normalized_upper = normalized.str.upper()
                allowed = {
                    str(value).strip().upper()
                    for value in (rules.get("unique_values") or [])
                }
                unseen_mask = normalized_upper.notna() & ~normalized_upper.isin(allowed)
                self._record_issue(unseen_mask, col)
                normalized = normalized.mask(unseen_mask)

            self.df[col] = normalized

    def drop_corrupted_rows(self, threshold: float = settings.DATA_QUALITY_ROW_ISSUE_THRESHOLD):
        denominator = max(len(self.schema), 1)
        row_issue_ratio = self.issue_counts / denominator
        removal_mask = row_issue_ratio >= threshold

        if bool(removal_mask.any()):
            self.removed_rows = self.df.loc[removal_mask].copy()
            self.df = self.df.loc[~removal_mask].copy()

        self.audit["rows_removed"] = int(removal_mask.sum())
        self.audit["rows_out"] = int(len(self.df))

    def handle_nulls(self):
        for col, dtype in self.schema.items():
            if col not in self.df.columns:
                continue

            rules = self.profile.get(col, {})

            if dtype in {"int", "float"}:
                series = pd.to_numeric(self.df[col], errors="coerce")
                non_null = series.dropna()
                fallback = non_null.median() if not non_null.empty else None
                if fallback is None or pd.isna(fallback):
                    fallback = rules.get("median", rules.get("mean"))
                if fallback is None or pd.isna(fallback):
                    if "min" in rules and "max" in rules:
                        fallback = (float(rules["min"]) + float(rules["max"])) / 2
                    else:
                        fallback = 0

                self.df[col] = series.fillna(float(fallback))
                continue

            if dtype == "bool":
                mode = self.df[col].dropna().mode()
                fallback = bool(mode.iloc[0]) if not mode.empty else False
                self.df[col] = self.df[col].fillna(fallback)
                continue

            if self._is_enum_column(col, rules):
                mode = self.df[col].dropna().astype(str).str.strip().mode()
                if not mode.empty:
                    fallback = mode.iloc[0]
                else:
                    allowed_values = rules.get("unique_values") or []
                    fallback = str(allowed_values[0]).strip() if allowed_values else "UNKNOWN"
            elif self._is_identifier_column(col):
                fallback = "UNKNOWN_ID"
            else:
                fallback = "UNKNOWN"

            self.df[col] = self.df[col].fillna(fallback).astype(str)

    def coerce_types(self):
        for col, dtype in self.schema.items():
            if col not in self.df.columns:
                continue

            try:
                if dtype == "int":
                    self.df[col] = pd.to_numeric(self.df[col], errors="coerce").round().astype("Int64")
                elif dtype == "float":
                    self.df[col] = pd.to_numeric(self.df[col], errors="coerce")
                elif dtype == "bool":
                    self.df[col] = self.df[col].astype("boolean")
            except Exception:
                pass

    def normalize_categoricals(self):
        for col, dtype in self.schema.items():
            if col not in self.df.columns:
                continue

            if dtype in {"int", "float", "bool"}:
                continue

            rules = self.profile.get(col, {})
            if self._is_enum_column(col, rules):
                self.df[col] = self.df[col].astype(str).str.strip().str.upper()
            else:
                self.df[col] = self.df[col].astype(str).str.strip()

    def run(self):
        self.normalize_missing_markers()
        self.sanitize_numeric_columns()
        self.sanitize_boolean_columns()
        self.sanitize_categoricals()
        self.drop_corrupted_rows()
        self.handle_nulls()
        self.coerce_types()
        self.normalize_categoricals()

        return self.df, {
            **self.audit,
            "removed_rows_preview": self.removed_rows.head(10).to_dict(orient="records"),
        }
