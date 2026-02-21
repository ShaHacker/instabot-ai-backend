from pydantic import BaseModel
from datetime import datetime


class LeadResponse(BaseModel):
    id: int
    ig_username: str
    full_name: str | None = None
    phone: str | None = None
    city: str | None = None
    product: str | None = None
    source_post_id: int | None = None
    source_post_caption: str | None = None
    status: str
    notes: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class LeadStatusUpdate(BaseModel):
    status: str  # new, contacted, converted


class LeadListResponse(BaseModel):
    leads: list[LeadResponse]
    total: int
    page: int
    pages: int
