from logging.config import fileConfig
import os
import sys

from dotenv import load_dotenv
from sqlalchemy import create_engine, pool
from sqlalchemy.engine import URL
from alembic import context

# Ensure app is importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Load models
from app.models.base import Base
from app.models.tenant_tables import TENANT_MODELS

#  ensure all models are imported
from app.models import (
    MLModel,
    PipelineRun,
    PredictionLog,
    Incident,
    DriftFinding,
    DataQualityFinding,
    Tenant,
    User,
    AgentRun,
    AgentStepLog,
    RemediationRun,
    RemediationActionLog,
)

# Load environment variables
load_dotenv()

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata for Alembic
target_metadata = Base.metadata


# -----------------------------
# Database URL builder
# -----------------------------
def get_database_url():
    return URL.create(
        drivername="postgresql+psycopg2",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 5432)),
        database=os.getenv("DB_NAME"),
    )


# -----------------------------
# Filter: Ignore Django tables
# -----------------------------
def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table":
        if name.startswith("django_") or name.startswith("auth_"):
            return False
        if name in {model.__tablename__ for model in TENANT_MODELS}:
            return False
    return True


# -----------------------------
# Offline migrations
# -----------------------------
def run_migrations_offline() -> None:
    url = get_database_url()

    context.configure(
        url=str(url),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},

        include_object=include_object, 

        # include_object=include_object,

    )

    with context.begin_transaction():
        context.run_migrations()


# -----------------------------
# Online migrations
# -----------------------------
def run_migrations_online() -> None:
    url = get_database_url()

    connectable = create_engine(
        url,
        poolclass=pool.NullPool,
        connect_args={"sslmode": "require"},  # Required for Supabase
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,


            include_object=include_object,

            # include_object=include_object,  # 


            

        )

        with context.begin_transaction():
            context.run_migrations()


# -----------------------------
# Entry point
# -----------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
