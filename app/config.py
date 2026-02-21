from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/instabot_ai"
    DATABASE_URL_SYNC: str = "postgresql://user:password@localhost:5432/instabot_ai"

    # JWT
    SECRET_KEY: str = "your-super-secret-key-change-this"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # Google Gemini
    GEMINI_API_KEY: str = ""

    # Instagram / Meta
    META_APP_ID: str = ""
    META_APP_SECRET: str = ""
    META_WEBHOOK_VERIFY_TOKEN: str = "instabot-verify-token"
    INSTAGRAM_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/instagram/callback"

    # Frontend URL
    FRONTEND_URL: str = "http://localhost:5173"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
