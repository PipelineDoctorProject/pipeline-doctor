from datetime import datetime
import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship

from app.models.base import Base


class SlackWorkspace(Base):
    __tablename__ = "slack_workspaces"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id = Column(String, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, unique=True)
    slack_team_id = Column(String, nullable=False, unique=True)
    slack_team_name = Column(String, nullable=False)
    bot_token = Column(String, nullable=False)
    bot_user_id = Column(String, nullable=True)
    scope = Column(String, nullable=True)
    connected_by_user_id = Column(String, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    connected_by_slack_user_id = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    channels = relationship("SlackChannel", back_populates="workspace", cascade="all, delete-orphan")
