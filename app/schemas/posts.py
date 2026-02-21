from pydantic import BaseModel
from datetime import datetime


class KeywordCreate(BaseModel):
    keyword: str
    reply_text: str
    reply_type: str = "comment"  # comment, dm, both


class KeywordResponse(BaseModel):
    id: int
    keyword: str
    reply_text: str
    reply_type: str
    created_at: datetime

    class Config:
        from_attributes = True


class PostResponse(BaseModel):
    id: int
    ig_post_id: str
    ig_media_url: str | None = None
    ig_thumbnail_url: str | None = None
    caption: str | None = None
    media_type: str | None = None
    permalink: str | None = None
    automation_enabled: bool
    created_at: datetime
    ig_created_at: datetime | None = None

    class Config:
        from_attributes = True


class PostDetailResponse(PostResponse):
    keywords: list[KeywordResponse] = []


class PostToggle(BaseModel):
    automation_enabled: bool
