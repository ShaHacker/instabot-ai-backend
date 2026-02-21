from pydantic import BaseModel
from datetime import datetime


class QACreate(BaseModel):
    question: str
    answer: str


class QAUpdate(BaseModel):
    question: str | None = None
    answer: str | None = None


class QAResponse(BaseModel):
    id: int
    question: str
    answer: str
    created_at: datetime

    class Config:
        from_attributes = True
