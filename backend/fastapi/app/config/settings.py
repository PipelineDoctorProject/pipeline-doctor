import os
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load .env file
load_dotenv()


def _int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value in (None, ""):
        return default
    return int(raw_value)


def _float_env(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if raw_value in (None, ""):
        return default
    return float(raw_value)


BASELINE_UPLOAD_DIR = "uploads/baselines"
os.makedirs(BASELINE_UPLOAD_DIR, exist_ok=True)

CLEANED_OUTPUT_DIR = os.getenv("CLEANED_OUTPUT_DIR", "cleaned")
QUARANTINE_OUTPUT_DIR = os.getenv("QUARANTINE_OUTPUT_DIR", os.path.join(CLEANED_OUTPUT_DIR, "quarantine"))
os.makedirs(CLEANED_OUTPUT_DIR, exist_ok=True)
os.makedirs(QUARANTINE_OUTPUT_DIR, exist_ok=True)

# Application artifact storage. Local filesystem remains the development default.
# Production should use Azure Blob Storage.
APP_STORAGE_BACKEND = os.getenv("APP_STORAGE_BACKEND", "local").lower()
APP_STORAGE_LOCAL_ROOT = os.getenv("APP_STORAGE_LOCAL_ROOT", ".")
AZURE_APP_STORAGE_CONNECTION_STRING = os.getenv("AZURE_APP_STORAGE_CONNECTION_STRING")
AZURE_APP_STORAGE_CONTAINER = os.getenv("AZURE_APP_STORAGE_CONTAINER", "app-artifacts")


# JWT Config
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# DB Config
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = _int_env("DB_PORT", 5432)
DB_NAME = os.getenv("DB_NAME")
DB_SSLMODE = os.getenv("DB_SSLMODE", "require")
DB_POOL_SIZE = _int_env("DB_POOL_SIZE", 4)
DB_MAX_OVERFLOW = _int_env("DB_MAX_OVERFLOW", 0)
DB_POOL_TIMEOUT = _int_env("DB_POOL_TIMEOUT", 15)
DB_POOL_RECYCLE = _int_env("DB_POOL_RECYCLE", 300)

MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
MAIL_FROM = os.getenv("MAIL_FROM")
MAIL_PORT = _int_env("MAIL_PORT", 587)
MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME", "OpsSight.ai")
EVIDENTLY_TOKEN = os.getenv("EVIDENTLY_TOKEN")
EVIDENTLY_PROJECT_ID = os.getenv("EVIDENTLY_PROJECT_ID")
EVIDENTLY_PROJECT_NAME = os.getenv("EVIDENTLY_PROJECT_NAME", "pipeline-doctor")

# Runtime service URLs
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://127.0.0.1:5000")
LOCAL_MLFLOW_URIS = {
    "http://127.0.0.1:5000",
    "http://localhost:5000",
}
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
SLACK_CLIENT_ID = os.getenv("SLACK_CLIENT_ID")
SLACK_CLIENT_SECRET = os.getenv("SLACK_CLIENT_SECRET")
SLACK_REDIRECT_URI = os.getenv("SLACK_REDIRECT_URI")
SLACK_BOT_SCOPES = os.getenv(
    "SLACK_BOT_SCOPES",
    "chat:write,chat:write.public,channels:read,channels:join,groups:read",
)

# Data quality defaults
DATA_QUALITY_NULL_RATIO_THRESHOLD = _float_env("DATA_QUALITY_NULL_RATIO_THRESHOLD", 0.30)
DATA_QUALITY_ROW_ISSUE_THRESHOLD = _float_env("DATA_QUALITY_ROW_ISSUE_THRESHOLD", 0.70)
DATA_QUALITY_MIN_CLEAN_ROW_COUNT = _int_env("DATA_QUALITY_MIN_CLEAN_ROW_COUNT", 10)
DATA_QUALITY_MIN_CLEAN_ROW_RATIO = _float_env("DATA_QUALITY_MIN_CLEAN_ROW_RATIO", 0.50)
DATA_QUALITY_CATEGORICAL_LIMIT = _int_env("DATA_QUALITY_CATEGORICAL_LIMIT", 50)
DATA_QUALITY_HIGH_CARDINALITY_LIMIT = _int_env("DATA_QUALITY_HIGH_CARDINALITY_LIMIT", 200)
DATA_QUALITY_HIGH_CARDINALITY_RATIO = _float_env("DATA_QUALITY_HIGH_CARDINALITY_RATIO", 0.20)

# Remediation and retraining defaults
REMEDIATION_MIN_TRAINING_ROWS = _int_env("REMEDIATION_MIN_TRAINING_ROWS", 25)
REMEDIATION_MAX_TARGET_NULL_RATIO = _float_env("REMEDIATION_MAX_TARGET_NULL_RATIO", 0.10)
REMEDIATION_MAX_CLASS_COUNT = _int_env("REMEDIATION_MAX_CLASS_COUNT", 20)
REMEDIATION_MAX_CLASS_UNIQUE_RATIO = _float_env("REMEDIATION_MAX_CLASS_UNIQUE_RATIO", 0.35)
REMEDIATION_MIN_CLASS_COUNT = _int_env("REMEDIATION_MIN_CLASS_COUNT", 3)
REMEDIATION_TEST_SIZE = _float_env("REMEDIATION_TEST_SIZE", 0.20)
REMEDIATION_STAGING_ALIAS = os.getenv("REMEDIATION_STAGING_ALIAS", "staging")
REMEDIATION_CHAMPION_ALIAS = os.getenv("REMEDIATION_CHAMPION_ALIAS", "champion")
REMEDIATION_PROMOTION_ALIAS = os.getenv("REMEDIATION_PROMOTION_ALIAS", REMEDIATION_STAGING_ALIAS)
REMEDIATION_TASK_SOFT_TIME_LIMIT_SECONDS = _int_env("REMEDIATION_TASK_SOFT_TIME_LIMIT_SECONDS", 300)
REMEDIATION_TASK_TIME_LIMIT_SECONDS = _int_env("REMEDIATION_TASK_TIME_LIMIT_SECONDS", 360)
REMEDIATION_MLFLOW_REQUEST_TIMEOUT_SECONDS = _int_env("REMEDIATION_MLFLOW_REQUEST_TIMEOUT_SECONDS", 30)
REMEDIATION_MLFLOW_MAX_RETRIES = _int_env("REMEDIATION_MLFLOW_MAX_RETRIES", 1)
REMEDIATION_CANDIDATE_MLFLOW_TRACKING_URI = os.getenv(
    "REMEDIATION_CANDIDATE_MLFLOW_TRACKING_URI",
    MLFLOW_TRACKING_URI,
)
REMEDIATION_MLFLOW_RUN_ARTIFACT_PATHS = [
    path.strip()
    for path in os.getenv("REMEDIATION_MLFLOW_RUN_ARTIFACT_PATHS", "model").split(",")
    if path.strip()
]


def get_allowed_origins() -> list[str]:
    origins = {FRONTEND_URL}
    parsed = urlparse(FRONTEND_URL)

    if parsed.hostname == "localhost":
        origins.add(FRONTEND_URL.replace("localhost", "127.0.0.1"))
    elif parsed.hostname == "127.0.0.1":
        origins.add(FRONTEND_URL.replace("127.0.0.1", "localhost"))

    return sorted(origins)


def get_auth_cookie_settings() -> dict[str, object]:
    parsed = urlparse(FRONTEND_URL)
    is_local_http = parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1"}
    secure = not is_local_http

    return {
        "httponly": True,
        "secure": secure,
        "samesite": "Lax" if not secure else "None",
        "path": "/",
    }


def resolve_mlflow_tracking_uri(configured_uri: str | None = None) -> str:
    # Existing DB rows often store localhost, which is wrong from inside Docker.
    if configured_uri and configured_uri not in LOCAL_MLFLOW_URIS:
        return configured_uri

    if configured_uri in LOCAL_MLFLOW_URIS and MLFLOW_TRACKING_URI not in LOCAL_MLFLOW_URIS:
        return MLFLOW_TRACKING_URI

    return configured_uri or MLFLOW_TRACKING_URI
