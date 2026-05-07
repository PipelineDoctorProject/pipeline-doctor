from sqlalchemy import Column, String
from app.models.base import Base
import uuid

class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String)
    schema_name = Column(String, unique=True)