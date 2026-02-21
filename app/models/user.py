from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    gemini_api_key = Column(String(255), nullable=True)
    ai_tone = Column(String(50), default="friendly")
    custom_tone = Column(String(500), nullable=True)
    default_language = Column(String(50), default="English")
    email_notifications = Column(Boolean, default=False)
    daily_summary = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    ig_account = relationship("IGAccount", back_populates="user", uselist=False)
    posts = relationship("Post", back_populates="user")
    qa_pairs = relationship("QAPair", back_populates="user")
    dm_flows = relationship("DMFlow", back_populates="user")
    leads = relationship("Lead", back_populates="user")
    activity_logs = relationship("ActivityLog", back_populates="user")
