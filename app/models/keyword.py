from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from datetime import datetime, timezone
from app.database import Base
from sqlalchemy.orm import relationship


class Keyword(Base):
    __tablename__ = "keywords"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    keyword = Column(String(255), nullable=False)
    reply_text = Column(Text, nullable=False)
    reply_type = Column(String(50), default="comment")  # comment, dm, both
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    post = relationship("Post", back_populates="keywords")
