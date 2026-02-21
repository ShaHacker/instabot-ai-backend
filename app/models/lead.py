from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ig_username = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    city = Column(String(255), nullable=True)
    product = Column(String(255), nullable=True)
    source_post_id = Column(Integer, ForeignKey("posts.id"), nullable=True)
    status = Column(String(50), default="new")  # new, contacted, converted
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="leads")
    source_post = relationship("Post")
    conversations = relationship("Conversation", back_populates="lead")
