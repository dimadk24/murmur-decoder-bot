import logging
from pydantic import Field

from pydantic_settings import BaseSettings, SettingsConfigDict

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger('httpx').setLevel(logging.WARNING)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # .env.local takes priority over .env
        env_file=(".env", ".env.local")
    )
    IS_LOCAL: bool = Field()
    # https://core.telegram.org/bots/api#:~:text=all%20pending%20updates-,secret_token,-String
    SECRET_KEY: str = Field(min_length=16, pattern=f"^[A-Za-z0-9_-]+$")
    TELEGRAM_BOT_TOKEN: str = Field()
    OPEN_AI_API_KEY: str = Field()
    DOMAIN: str = Field()


app_config = Settings()
