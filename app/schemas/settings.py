from pydantic import BaseModel


class SettingsUpdate(BaseModel):
    gemini_api_key: str | None = None
    ai_tone: str | None = None
    custom_tone: str | None = None
    default_language: str | None = None
    email_notifications: bool | None = None
    daily_summary: bool | None = None


class SettingsResponse(BaseModel):
    gemini_api_key: str | None = None
    ai_tone: str
    custom_tone: str | None = None
    default_language: str
    email_notifications: bool
    daily_summary: bool
    ig_connected: bool = False
    ig_username: str | None = None
    ig_profile_pic: str | None = None

    class Config:
        from_attributes = True
