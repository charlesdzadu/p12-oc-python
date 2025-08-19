import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    database_url: str = Field(default="sqlite:///./epicevents.db")
    jwt_secret_key: str = Field(default="change-this-in-production")
    jwt_algorithm: str = Field(default="HS256")
    jwt_expiration_hours: int = Field(default=24)
    sentry_dsn: Optional[str] = Field(default=None)
    app_env: str = Field(default="development")
    debug: bool = Field(default=False)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()


PROJECT_ROOT = Path(__file__).parent.parent.parent
TOKEN_FILE = PROJECT_ROOT / ".epicevents_token"
