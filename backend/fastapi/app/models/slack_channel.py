from datetime import datetime
import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.models.base import Base


class SlackChannel(Base):
    __tablename__ = "slack_channels"
    __table_args__ = (
        UniqueConstraint("workspace_id", "slack_channel_id", name="uq_slack_workspace_channel"),
    )

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id = Column(String, ForeignKey("slack_workspaces.id", ondelete="CASCADE"), nullable=False)
    slack_channel_id = Column(String, nullable=False)
    slack_channel_name = Column(String, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    workspace = relationship("SlackWorkspace", back_populates="channels")
