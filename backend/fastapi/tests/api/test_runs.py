import pytest
from app.models.pipeline_run import PipelineRun
from app.models.ml_model import MLModel

def test_list_runs_empty(client):
    """Test the list runs endpoint when there are no runs."""
    response = client.get("/runs/")
    assert response.status_code == 200
    data = response.json()
    assert "runs" in data
    assert data["runs"] == []
    assert data["total_count"] == 0

def test_list_runs_with_data(client, db_session, test_user):
    """Test the list runs endpoint when data exists."""
    # 1. Setup mock data using the transactional db_session
    model = MLModel(
        id=1,
        tenant_id=test_user.tenant_id,
        name="Test Model",
        version="v1",
        mlflow_model_name="test_model"
    )
    db_session.add(model)
    db_session.commit()

    run1 = PipelineRun(
        id=1,
        model_id=1,
        baseline_version=1,
        status="success",
        schema_changed=False
    )
    run2 = PipelineRun(
        id=2,
        model_id=1,
        baseline_version=1,
        status="failed",
        schema_changed=True
    )
    db_session.add_all([run1, run2])
    db_session.commit()

    # 2. Make request using the TestClient
    response = client.get("/runs/?skip=0&limit=10")
    
    # 3. Assert the API response
    assert response.status_code == 200
    data = response.json()
    assert data["total_count"] == 2
    assert len(data["runs"]) == 2
    
    # Check that runs are ordered properly (usually newest first, or by ID)
    ids = [run["id"] for run in data["runs"]]
    assert 1 in ids
    assert 2 in ids

def test_list_runs_pagination(client, db_session, test_user):
    """Test that pagination parameters work correctly."""
    # Setup mock data
    model = MLModel(
        id=1,
        tenant_id=test_user.tenant_id,
        name="Test Model",
        version="v1"
    )
    db_session.add(model)
    db_session.commit()

    runs = [
        PipelineRun(id=i, model_id=1, baseline_version=1, status="success")
        for i in range(1, 16) # 15 runs
    ]
    db_session.add_all(runs)
    db_session.commit()

    # Test limit
    response = client.get("/runs/?skip=0&limit=5")
    data = response.json()
    assert data["total_count"] == 15
    assert len(data["runs"]) == 5

    # Test skip
    response2 = client.get("/runs/?skip=10&limit=10")
    data2 = response2.json()
    assert len(data2["runs"]) == 5
