import os
import pandas as pd
from sqlalchemy.orm import Session

from app.models.pipeline_run import PipelineRun
from app.services.drift.utils import get_baseline_file_for_model
from app.services.drift.data_drift import check_data_drift, check_profile_drift
from app.services.drift.concept_drift import check_concept_drift
from app.services.drift.storage import save_drift_finding_and_incident
from app.services.incidents.live_events import publish_incident_event
from app.services.quality.baseline_service import get_active_baseline
def run_drift_checks(db: Session, run: PipelineRun, tenant_id: str | None = None):
    if not run.cleaned_data_path or not os.path.exists(run.cleaned_data_path):
        message = f"Cleaned data not found for run {run.id}: {run.cleaned_data_path}"
        print(message)
        return {"saved": 0, "reason": message}

    active_baseline = get_active_baseline(db, run.model_id)
    baseline_file = get_baseline_file_for_model(active_baseline)
    current_data = pd.read_csv(run.cleaned_data_path)

    reference_data = None
    data_results = []
    feature_names = []
    concept_results = []

    if baseline_file:
        try:
            reference_data = pd.read_csv(baseline_file)
            print(
                "Running drift with raw baseline "
                f"baseline={baseline_file}, cleaned={run.cleaned_data_path}, "
                f"reference_cols={list(reference_data.columns)}, current_cols={list(current_data.columns)}"
            )
            data_results, feature_names = check_data_drift(reference_data, current_data.copy())
        except Exception as exc:
            print(f"Raw baseline drift failed for run {run.id}: {exc}")
    else:
        print(f"Raw baseline file not found for model {run.model_id}; using profile drift fallback.")

    if not data_results:
        print(f"Using profile drift fallback for run {run.id}.")
        data_results, feature_names = check_profile_drift(current_data.copy(), active_baseline.profile)
    
    # 2. Concept Drift (Predictions)
    if reference_data is not None:
        concept_results = check_concept_drift(db, run.id, reference_data, feature_names)

    # 3. Save all results
    all_results = data_results + concept_results
    if not all_results:
        message = (
            "No drift metrics were saved because no comparable columns "
            f"were found in the active baseline profile. "
            f"current_cols={list(current_data.columns)}"
        )
        print(message)
        return {"saved": 0, "reason": message}

    created_incidents = []
    for res in all_results:
        incident = save_drift_finding_and_incident(
            db=db,
            run_id=run.id,
            feature_name=res["feature_name"],
            psi_score=res["psi_score"],
            ks_score=res["ks_score"],
            ks_pvalue=res["ks_pvalue"],
            drift_score=res["drift_score"],
            severity=res["severity"],
            finding_type_name=res["type"]
        )
        if incident:
            created_incidents.append(incident)

    db.commit()

    for incident in created_incidents:
        publish_incident_event("incident_created", incident)

    return {
        "saved": len(all_results),
        "reason": None,
        "created_incidents": len(created_incidents),
        "notification_strategy": "ui_events_only_for_drift_findings",
    }
