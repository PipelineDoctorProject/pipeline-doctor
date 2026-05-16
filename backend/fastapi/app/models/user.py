from sqlalchemy import Column, String, Boolean, ForeignKey
from app.models.base import Base
import uuid


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=True)
    tenant_id = Column(String,ForeignKey("tenants.id", ondelete="CASCADE" ),nullable=True)
    is_verified = Column(Boolean, default=False)
    otp_code = Column(String, nullable=True)
    role = Column(String, default="member")
    invite_token = Column(String, nullable=True)
    invite_accepted = Column(Boolean, default=False)