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
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
    abs_upload_dir = os.path.join(base_dir, BASELINE_UPLOAD_DIR)
    list_of_files = glob.glob(os.path.join(abs_upload_dir, '*.csv'))
    if not list_of_files:
        return None
    return max(list_of_files, key=os.path.getctime)
