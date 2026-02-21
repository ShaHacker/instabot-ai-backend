from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ig_post_id = Column(String(100), unique=True, nullable=False)
    ig_media_url = Column(String(500), nullable=True)
    ig_thumbnail_url = Column(String(500), nullable=True)
    caption = Column(Text, nullable=True)
    media_type = Column(String(50), nullable=True)
    permalink = Column(String(500), nullable=True)
    automation_enabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    ig_created_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="posts")
    keywords = relationship("Keyword", back_populates="post", cascade="all, delete-orphan")
