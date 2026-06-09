from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy import event
from sqlalchemy.orm import sessionmaker
from fastapi import Depends
from app.utils.schema_utils import apply_session_schema, set_schema

from app.config.settings import (
    DB_USER,
    DB_PASSWORD,
    DB_HOST,
    DB_PORT,
    DB_NAME,
    DB_SSLMODE,
    DB_POOL_SIZE,
    DB_MAX_OVERFLOW,
    DB_POOL_TIMEOUT,
    DB_POOL_RECYCLE,
)

# Build DB URL
DATABASE_URL = URL.create(
    drivername="postgresql+psycopg2",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT,
    database=DB_NAME,
)


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=DB_POOL_RECYCLE,
    pool_timeout=DB_POOL_TIMEOUT,
    pool_size=DB_POOL_SIZE,
    max_overflow=DB_MAX_OVERFLOW,
    connect_args={
        "sslmode": DB_SSLMODE,
        "connect_timeout": 5,
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
    },
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


@event.listens_for(SessionLocal, "after_begin")
def apply_tenant_schema_after_begin(session, transaction, connection):
    apply_session_schema(session, connection)


from fastapi import Request
from typing import Generator

def get_db(request: Request = None) -> Generator:
    # If the middleware already set up a db session, use it!
    if request and hasattr(request.state, "db") and request.state.db:
        yield request.state.db
        return
        
    # Fallback for background tasks or non-middleware requests
    db = SessionLocal()
    try:
        if request and getattr(request.state, "schema", None):
            set_schema(db, request.state.schema)
        yield db
    finally:
        db.close()


