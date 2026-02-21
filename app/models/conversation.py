from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"), nullable=False)
    flow_id = Column(Integer, ForeignKey("dm_flows.id"), nullable=True)
    ig_sender_id = Column(String(100), nullable=False)
    messages = Column(JSON, default=list)
    current_step = Column(Integer, default=0)
    status = Column(String(50), default="active")  # active, completed, abandoned
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    lead = relationship("Lead", back_populates="conversations")
    flow = relationship("DMFlow", back_populates="conversations")
