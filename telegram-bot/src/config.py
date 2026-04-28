import socket
from typing import Optional
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.logging_config import setup_logging


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    TZ: str = "Europe/Kyiv"
    API_URL: str = "http://backend:8000/api"
    REDIS_URL: str = "redis://vms-redis:6379/0"

    BOT_TOKEN: str
    API_KEY: str
    LIVING_COMPLEX_NAME: str

    GUARD_DASHBOARD_URL: Optional[str] = None

    @computed_field
    @property
    def HEADERS(self) -> dict:
        return {
            "X-API-Key": self.API_KEY,
            "Content-Type": "application/json"
        }

    @computed_field
    @property
    def REDIS_CONSUMER_NAME(self) -> str:
        hostname = socket.gethostname()
        return f"bot_consumer_{hostname}"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        setup_logging()


settings = Settings()
