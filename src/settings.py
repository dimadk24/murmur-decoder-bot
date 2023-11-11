import logging
from typing import Optional
from pydantic import Field

from pydantic_settings import BaseSettings, SettingsConfigDict

from logtail import LogtailHandler
import sentry_sdk


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
    LOG_LEVEL: str = Field(default=logging.INFO)
    LOGTAIL_TOKEN: Optional[str] = Field()
    SENTRY_DSN: Optional[str] = Field()


app_config = Settings()


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=app_config.LOG_LEVEL,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

if not app_config.IS_LOCAL:
    handler = LogtailHandler(source_token=app_config.LOGTAIL_TOKEN)
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)

    def before_breadcrumb(crumb, hint):
        if crumb["category"] == "httplib" and crumb["data"] and crumb["data"]["url"]:
            url: str = crumb["data"]["url"]
            crumb["data"]["url"] = url.replace(
                app_config.TELEGRAM_BOT_TOKEN,
                f"****{app_config.TELEGRAM_BOT_TOKEN[-4:]}",
            )
        return crumb

    sentry_sdk.init(
        dsn=app_config.SENTRY_DSN,
        traces_sample_rate=0.1,
        profiles_sample_rate=0.1,
        before_breadcrumb=before_breadcrumb,
    )
