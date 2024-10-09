import urllib.parse
from logging.config import dictConfig
import google.cloud.logging

import sentry_sdk

from settings import app_config
from redacting_formatter import RedactingFormatter


def mask_bot_token(string: str) -> str:
    return string.replace(
        app_config.TELEGRAM_BOT_TOKEN,
        "[--redacted--]"
    ).replace(
        urllib.parse.quote_plus(app_config.TELEGRAM_BOT_TOKEN),
        "[--redacted--]"
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
    google_logging_client = google.cloud.logging.Client()

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "loggers": {
            "root": {
                "level": "INFO",
                "handlers":
                    ["cloud_logging_handler",
                     "consoleHandler"] if app_config.USE_LOGGING_INTEGRATIONS
                    else ["consoleHandler"]
            },
            "murmur": {
                "level": app_config.LOG_LEVEL,
                "propagate": False,
                "handlers":
                    ["cloud_logging_handler",
                     "consoleHandler"] if app_config.USE_LOGGING_INTEGRATIONS
                    else ["consoleHandler"]
            }
        },
        "handlers": {
            "cloud_logging_handler": {
                "class": google.cloud.logging.handlers.CloudLoggingHandler,
                "client": google_logging_client,
                "formatter": "gcloudFormatter",
                "labels": {
                    "service": "murmur-decoder-bot"
                },
            },
            "consoleHandler": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
                "formatter": "consoleFormatter",
                "stream": "ext://sys.stdout",
            },
        },
        "formatters": {
            "consoleFormatter": {
                "()": RedactingFormatter,
                "patterns": [
                    app_config.TELEGRAM_BOT_TOKEN,
                    app_config.SECRET_KEY,
                ],
                "format": "[%(asctime)s] %(name)s - %(levelname)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "gcloudFormatter": {
                "()": RedactingFormatter,
                "patterns": [
                    app_config.TELEGRAM_BOT_TOKEN,
                    app_config.SECRET_KEY,
                ],
                "format": "%(name)s - %(levelname)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
    }
    dictConfig(logging_config)

    if app_config.USE_LOGGING_INTEGRATIONS:
        sentry_sdk.init(
            dsn=app_config.SENTRY_DSN,
            traces_sample_rate=0.1,
            profiles_sample_rate=0.1,
            before_breadcrumb=before_sentry_breadcrumb,
        )
