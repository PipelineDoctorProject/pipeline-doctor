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