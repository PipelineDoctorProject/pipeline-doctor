from __future__ import annotations

from typing import Any

import pandas as pd

from app.config import settings
from app.services.quality.baseline import _is_identifier_column
from app.services.quality.column_classifier import classify_column
from app.services.quality.type_utils import normalize_dtype


def build_feature_candidates(df: pd.DataFrame, new_columns: list[str]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    row_count = int(len(df))

    for column in new_columns:
        if column not in df.columns:
            continue

        series = df[column]
        non_null = series.dropna()
        dtype = normalize_dtype(series.dtype)
        inferred_type = classify_column(series)
        unique_count = int(non_null.astype(str).nunique()) if not non_null.empty else 0
        missing_ratio = float(series.isna().mean()) if row_count else 0.0
        sample_values = non_null.astype(str).unique()[:10].tolist()

        candidate = {
            "column": column,
            "dtype": dtype,
            "inferred_type": inferred_type,
            "missing_ratio": missing_ratio,
            "unique_count": unique_count,
            "row_count": row_count,
            "sample_values": sample_values,
            "safe_as_feature": False,
            "recommended_decision": "monitor_only",
            "encoding_strategy": None,
            "reason": "Column requires review before it can become a model feature.",
        }

        if _is_identifier_column(column):
            candidate.update(
                {
                    "semantic_type": "identifier",
                    "recommended_decision": "reject_as_feature",
                    "reason": "Identifier-like columns are not safe model features by default.",
                }
            )
        elif inferred_type in {"numeric", "boolean"}:
            candidate.update(
                {
                    "semantic_type": "numeric_feature",
                    "safe_as_feature": True,
                    "recommended_decision": "approve_as_feature",
                    "encoding_strategy": "none",
                    "reason": "Numeric columns can be used directly after validation.",
                }
            )
        elif inferred_type == "categorical" and _is_high_cardinality_candidate(
            unique_count,
            len(non_null),
        ):
            candidate.update(
                {
                    "semantic_type": "high_cardinality_text",
                    "recommended_decision": "reject_as_feature",
                    "encoding_strategy": "custom_required",
                    "reason": "High-cardinality strings can leak identity or dominate model behavior.",
                }
            )
        elif inferred_type == "categorical":
            candidate.update(
                {
                    "semantic_type": "categorical_feature",
                    "safe_as_feature": True,
                    "recommended_decision": "approve_with_encoding",
                    "encoding_strategy": "one_hot",
                    "reason": "Low-cardinality categorical strings can be encoded after admin approval.",
                }
            )

        candidates.append(candidate)

    return candidates


def _is_high_cardinality_candidate(unique_count: int, row_count: int) -> bool:
    if unique_count >= settings.DATA_QUALITY_HIGH_CARDINALITY_LIMIT:
        return True

    if row_count < 50:
        return False

    return (unique_count / max(row_count, 1)) >= settings.DATA_QUALITY_HIGH_CARDINALITY_RATIO


def profile_from_feature_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    if candidate.get("inferred_type") in {"numeric", "boolean"}:
        return {
            "type": "numeric" if candidate.get("inferred_type") == "numeric" else "categorical",
            "validation_mode": "range" if candidate.get("inferred_type") == "numeric" else "enum",
            "feature_candidate": True,
            "encoding_strategy": candidate.get("encoding_strategy"),
            "sample_values": candidate.get("sample_values", []),
        }

    if candidate.get("semantic_type") == "high_cardinality_text":
        return {
            "type": "text",
            "validation_mode": "high_cardinality",
            "feature_candidate": True,
            "encoding_strategy": "custom_required",
            "sample_values": candidate.get("sample_values", []),
        }

    if candidate.get("semantic_type") == "identifier":
        return {
            "type": "identifier",
            "validation_mode": "identifier",
            "feature_candidate": False,
            "sample_values": candidate.get("sample_values", []),
        }

    return {
        "type": "categorical",
        "validation_mode": "enum",
        "feature_candidate": True,
        "encoding_strategy": candidate.get("encoding_strategy") or "one_hot",
        "unique_values": candidate.get("sample_values", [])[
            : settings.DATA_QUALITY_CATEGORICAL_LIMIT
        ],
    }


def normalize_approved_feature_columns(
    approved_columns: list[str] | None,
    candidates: list[dict[str, Any]] | None,
) -> list[str]:
    if not approved_columns or not candidates:
        return []

    candidate_by_name = {str(item.get("column")): item for item in candidates}
    approved: list[str] = []
    for column in approved_columns:
        name = str(column or "").strip()
        candidate = candidate_by_name.get(name)
        if not candidate or not candidate.get("safe_as_feature"):
            continue
        if name not in approved:
            approved.append(name)

    return approved
