from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker
from fastapi import Depends
from app.utils.schema_utils import set_schema

from app.config.settings import (
    DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME
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
    connect_args={"sslmode": "require"},
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


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
        yield db
    finally:
        db.close()


