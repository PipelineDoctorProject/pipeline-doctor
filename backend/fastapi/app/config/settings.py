import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()


BASELINE_UPLOAD_DIR = "uploads/baselines"
os.makedirs(BASELINE_UPLOAD_DIR, exist_ok=True)


# JWT Config
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")

# DB Config
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME")

MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
MAIL_FROM = os.getenv("MAIL_FROM")
MAIL_PORT = int(os.getenv("MAIL_PORT"))
MAIL_SERVER = os.getenv("MAIL_SERVER")
MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME")
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


def resolve_mlflow_tracking_uri(configured_uri: str | None = None) -> str:
    # Existing DB rows often store localhost, which is wrong from inside Docker.
    if configured_uri and configured_uri not in LOCAL_MLFLOW_URIS:
        return configured_uri

    if configured_uri in LOCAL_MLFLOW_URIS and MLFLOW_TRACKING_URI not in LOCAL_MLFLOW_URIS:
        return MLFLOW_TRACKING_URI

    return configured_uri or MLFLOW_TRACKING_URI
