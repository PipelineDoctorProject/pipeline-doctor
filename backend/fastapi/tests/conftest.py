import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Setup mock environment BEFORE loading the app
os.environ["TESTING"] = "True"
os.environ["JWT_SECRET"] = "test_secret_key"

from app.main import app
from app.db.session import get_db
from app.models.base import Base
from app.dependencies.auth import require_tenant_user
from app.models.user import User

# In-memory SQLite for blazing fast tests.
# Note: Postgres-specific features (like JSONB or Schemas) may need to be mocked
# or worked around for pure unit tests using SQLite.
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def setup_database():
    """Create all tables in the test database once."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture()
def db_session(setup_database):
    """
    Creates a fresh sqlalchemy session for a test, wrapped in a transaction.
    Any changes made during the test will be rolled back automatically.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture()
def test_user():
    """Returns a mock user for authentication dependencies."""
    user = User(
        id="usr_test123",
        email="test@example.com",
        tenant_id="tenant_test123",
        role="admin"
    )
    # We mock schema_name to avoid triggering Postgres SET SCHEMA commands during tests
    user.schema_name = None 
    return user

@pytest.fixture()
def client(db_session, test_user):
    """
    Provides a FastAPI TestClient configured to use the test database
    and mock out authentication.
    """
    def override_get_db():
        yield db_session

    def override_require_tenant_user():
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[require_tenant_user] = override_require_tenant_user

    with TestClient(app) as test_client:
        yield test_client

    # Clean up overrides after test
    app.dependency_overrides.clear()
