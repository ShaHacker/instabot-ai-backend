from pydantic import BaseModel
from datetime import datetime
from typing import Any


class FlowStepCreate(BaseModel):
    bot_message: str
    expected_input_type: str = "text"  # text, phone, city, name, any
    field_name: str = "custom"  # name, phone, city, custom


class FlowCreate(BaseModel):
    name: str
    steps: list[FlowStepCreate]


class FlowUpdate(BaseModel):
    name: str | None = None
    steps: list[FlowStepCreate] | None = None
    is_active: bool | None = None


class FlowResponse(BaseModel):
    id: int
    name: str
    steps: list[Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
