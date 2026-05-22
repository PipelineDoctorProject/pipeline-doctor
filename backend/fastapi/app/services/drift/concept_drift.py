import pandas as pd
from sqlalchemy.orm import Session
from app.models.prediction_log import PredictionLog
from app.services.drift.metrics import calculate_psi, calculate_ks
from app.services.drift.utils import classify_drift_severity

def check_concept_drift(db: Session, run_id: int, reference_data: pd.DataFrame, feature_names: list):
    results = []
    prediction_logs = db.query(PredictionLog).filter(PredictionLog.run_id == run_id).all()
    
    if not prediction_logs:
        return results
        
    current_predictions = [log.prediction.get('value') for log in prediction_logs if log.prediction and 'value' in log.prediction]
    
    target_col = None
    for col in ["target", "prediction", "loan_risk", "value", "y", "score"]:
        if col in reference_data.columns:
            target_col = col
            break
            
    if not target_col:
        possible_targets = [c for c in reference_data.columns if c not in feature_names]
        if possible_targets:
            target_col = possible_targets[-1]
            
    if target_col and current_predictions:
        reference_predictions = reference_data[target_col].dropna().values
        current_preds_clean = pd.Series(current_predictions).dropna().values
        
        if len(reference_predictions) > 0 and len(current_preds_clean) > 0:
            psi_score = calculate_psi(reference_predictions, current_preds_clean)
            ks_score, ks_pvalue = calculate_ks(reference_predictions, current_preds_clean)
            drift_score = max(psi_score, ks_score)
            severity = classify_drift_severity(drift_score)
            
            results.append({
                "feature_name": "prediction_output",
                "psi_score": psi_score,
                "ks_score": ks_score,
                "ks_pvalue": ks_pvalue,
                "drift_score": drift_score,
                "severity": severity,
                "type": "concept_drift"
            })
            
    return results
