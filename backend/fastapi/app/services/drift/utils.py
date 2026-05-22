import os
import glob
from app.config.settings import BASELINE_UPLOAD_DIR


def _fastapi_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))


def classify_drift_severity(drift_score: float) -> str:
    if drift_score >= 0.5:
        return "critical"
    if drift_score >= 0.3:
        return "high"
    if drift_score >= 0.2:
        return "medium"
    return "low"

def get_latest_baseline_file():
    abs_upload_dir = os.path.join(_fastapi_root(), BASELINE_UPLOAD_DIR)
    list_of_files = glob.glob(os.path.join(abs_upload_dir, '*.csv'))
    if not list_of_files:
        return None
    return max(list_of_files, key=os.path.getctime)


def get_baseline_file_for_model(baseline):
    if not baseline:
        return None

    profile = baseline.profile or {}
    meta = profile.get("_meta") if isinstance(profile, dict) else None
    file_path = (meta or {}).get("source_file_path")

    if file_path:
        candidate_paths = [
            file_path,
            os.path.abspath(file_path),
            os.path.join(_fastapi_root(), file_path),
        ]

        for candidate_path in candidate_paths:
            if os.path.exists(candidate_path):
                return candidate_path

    return get_latest_baseline_file()
