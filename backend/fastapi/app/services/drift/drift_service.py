import os
import pandas as pd
from sqlalchemy.orm import Session

from app.models.pipeline_run import PipelineRun
from app.services.drift.utils import get_latest_baseline_file
from app.services.drift.data_drift import check_data_drift
from app.services.drift.concept_drift import check_concept_drift
from app.services.drift.storage import save_drift_finding_and_incident

def run_drift_checks(db: Session, run: PipelineRun):
    if not run.cleaned_data_path or not os.path.exists(run.cleaned_data_path):
        print("Cleaned data not found.")
        return

    baseline_file = get_latest_baseline_file()
    if not baseline_file:
        print("Baseline file not found.")
        return

    reference_data = pd.read_csv(baseline_file)
    current_data = pd.read_csv(run.cleaned_data_path)

    # 1. Data Drift (Features)
    data_results, feature_names = check_data_drift(reference_data, current_data)
    
    # 2. Concept Drift (Predictions)
    concept_results = check_concept_drift(db, run.id, reference_data, feature_names)

    # 3. Save all results
    all_results = data_results + concept_results
    for res in all_results:
        save_drift_finding_and_incident(
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

    db.commit()