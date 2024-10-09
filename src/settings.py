import logging
import os
from typing import Optional
from pydantic import Field

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # .env.local takes priority over .env
        env_file=(".env", ".env.local")
    )
    USE_WEBHOOK: bool = Field()
    USE_LOGGING_INTEGRATIONS: bool = Field()
    # https://core.telegram.org/bots/api#:~:text=all%20pending%20updates-,secret_token,-String
    SECRET_KEY: str = Field(min_length=16, pattern=f"^[A-Za-z0-9_-]+$")
    TELEGRAM_BOT_TOKEN: str = Field()
    OPEN_AI_API_KEY: str = Field()
    DOMAIN: str = Field()
    LOG_LEVEL: str | int = Field(default=logging.INFO)
    SENTRY_DSN: Optional[str] = Field()

    PORT: Optional[str] = Field(default="8000")


app_config = Settings()

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = (
    "google-application-credentials.json")
