import os
import glob
from app.config.settings import BASELINE_UPLOAD_DIR

def classify_drift_severity(drift_score: float) -> str:
    if drift_score >= 0.5:
        return "critical"
    if drift_score >= 0.3:
        return "high"
    if drift_score >= 0.2:
        return "medium"
    return "low"

def get_latest_baseline_file():
    list_of_files = glob.glob(os.path.join(BASELINE_UPLOAD_DIR, '*.csv'))
    if not list_of_files:
        return None
    return max(list_of_files, key=os.path.getctime)
