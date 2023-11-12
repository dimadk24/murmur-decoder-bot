import logging
from logtail import LogtailHandler
import sentry_sdk

from settings import app_config
from logging_mask_filter import RedactingFormatter


def mask_bot_token(string: str):
    string.replace(
        app_config.TELEGRAM_BOT_TOKEN,
        f"****{app_config.TELEGRAM_BOT_TOKEN[-2:]}",
    )


def before_sentry_breadcrumb(crumb, hint):
    if (
        crumb["category"] == "httplib"
        and crumb["data"]
        and crumb["data"]["url"]
    ):
        url: str = crumb["data"]["url"]
        crumb["data"]["url"] = mask_bot_token(url)
    return crumb


def init_logging():
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=app_config.LOG_LEVEL,
    )

    if app_config.USE_LOGGING_INTEGRATIONS:
        handler = LogtailHandler(source_token=app_config.LOGTAIL_TOKEN)
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)

        sentry_sdk.init(
            dsn=app_config.SENTRY_DSN,
            traces_sample_rate=0.1,
            profiles_sample_rate=0.1,
            before_breadcrumb=before_sentry_breadcrumb,
        )
    else:
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)

    for h in logging.root.handlers:
        h.setFormatter(
            RedactingFormatter(
                h.formatter,
                patterns=[
                    app_config.TELEGRAM_BOT_TOKEN,
                    app_config.SECRET_KEY,
                ],
            )
        )
