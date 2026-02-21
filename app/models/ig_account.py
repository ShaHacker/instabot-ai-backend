from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class IGAccount(Base):
    __tablename__ = "ig_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    ig_user_id = Column(String(100), nullable=False)
    ig_username = Column(String(255), nullable=True)
    ig_profile_pic = Column(String(500), nullable=True)
    access_token = Column(String(500), nullable=False)
    page_id = Column(String(100), nullable=True)
    page_access_token = Column(String(500), nullable=True)
    connected_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="ig_account")
