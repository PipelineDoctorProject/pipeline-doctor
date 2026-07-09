import pytest
from app.services.quality.pipeline import _evaluate_quality_gate

def test_evaluate_quality_gate_success():
    """Test quality gate passes when conditions are met."""
    result = _evaluate_quality_gate(
        cleaned_rows=1000,
        total_rows=1000,
        post_clean_result={"schema_errors": [], "summary": {"failed_checks": 0}},
        missing_cols=[]
    )
    
    assert result["status"] == "success"
    assert len(result["blocking_reasons"]) == 0
    assert result["clean_row_count"] == 1000

def test_evaluate_quality_gate_missing_cols():
    """Test quality gate fails if required baseline columns are missing."""
    result = _evaluate_quality_gate(
        cleaned_rows=1000,
        total_rows=1000,
        post_clean_result={"schema_errors": [], "summary": {"failed_checks": 0}},
        missing_cols=["age", "income"]
    )
    
    assert result["status"] == "failed"
    assert len(result["blocking_reasons"]) > 0
    assert any("missing baseline-required columns" in reason for reason in result["blocking_reasons"])

def test_evaluate_quality_gate_zero_rows():
    """Test quality gate fails if no rows remain after cleaning."""
    result = _evaluate_quality_gate(
        cleaned_rows=0,
        total_rows=100,
        post_clean_result={},
        missing_cols=[]
    )
    
    assert result["status"] == "failed"
    assert any("No usable rows remained" in reason for reason in result["blocking_reasons"])

def test_evaluate_quality_gate_failed_checks():
    """Test quality gate fails if data still fails validation checks after cleaning."""
    result = _evaluate_quality_gate(
        cleaned_rows=90,
        total_rows=100,
        post_clean_result={"schema_errors": [], "summary": {"failed_checks": 2}},
        missing_cols=[]
    )
    
    assert result["status"] == "failed"
    assert any("failed 2 validation checks" in reason for reason in result["blocking_reasons"])
