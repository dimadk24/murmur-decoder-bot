from settings import app_config

from io import BytesIO
import openai
from pathlib import Path
import logging

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
)

logger = logging.getLogger("murmur-main")

openai_client = openai.Client(api_key=app_config.OPEN_AI_API_KEY)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug("New start message")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Welcome! Send me your voice messages in any language",
    )


async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug("New message")
    if update.message.voice:
        logger.debug("Processing a voice message")

        file_id = update.message.voice.file_id
        tg_file = await context.bot.get_file(file_id)

        memory_file = BytesIO()
        await tg_file.download_to_memory(memory_file)
        memory_file.name = Path(tg_file.file_path).name
        logger.debug("Downloaded a voice message to memory")

        transcript = openai_client.audio.transcriptions.create(
            model="whisper-1", file=memory_file
        )
        logger.debug("Transcribed a voice message")

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=transcript.text,
            reply_to_message_id=update.message.id,
        )
        logger.info("Processed a voice message")
    else:
        logger.debug("New text message")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="I don't reply to texts, please send me a cute voice sample instead",
        )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.exception("Exception was raised during update processing")


if __name__ == "__main__":
    application = (
        ApplicationBuilder().token(app_config.TELEGRAM_BOT_TOKEN).build()
    )

    start_handler = CommandHandler("start", start)
    application.add_handler(start_handler)
    message_handler = MessageHandler(None, message)
    application.add_handler(message_handler)
    application.add_error_handler(error_handler)

    if app_config.USE_WEBHOOK:
        application.run_webhook(
            listen="0.0.0.0",
            port=3000,
            url_path="/webhook",
            secret_token=app_config.SECRET_KEY,
            webhook_url=f"https://{app_config.DOMAIN}/webhook",
        )
    else:
        application.run_polling()
