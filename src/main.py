import subprocess

from settings import app_config

from io import BytesIO
import openai
from pathlib import Path
import logging

from telegram import Update, File
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
)
from logger import init_logging

init_logging()

logger = logging.getLogger("murmur.main")

openai_client = openai.Client(api_key=app_config.OPEN_AI_API_KEY)

tmp_dir = Path('.tmp').resolve()
tmp_dir.mkdir(exist_ok=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.debug("New start message")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Welcome! Send me your voice messages in any language",
    )


async def download_tg_file(tg_file: File):
    extension = Path(tg_file.file_path).suffix
    download_path = tmp_dir / f"{tg_file.file_id}{extension}"

    await tg_file.download_to_drive(download_path)
    return download_path


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
    elif update.message.video_note:
        logger.debug("Processing a video note")

        tg_file = await update.message.video_note.get_file()
        video_path = await download_tg_file(tg_file)
        audio_path = video_path.with_suffix('.wav')

        subprocess.call([
            'ffmpeg',
            '-i', video_path,
            audio_path,
        ])

        transcript = openai_client.audio.transcriptions.create(
            model="whisper-1", file=audio_path
        )
        logger.debug("Transcribed a video note")

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=transcript.text,
            reply_to_message_id=update.message.id,
        )

        video_path.unlink()
        audio_path.unlink()
        logger.info("Processed a video note")
    else:
        logger.debug("The message type is not supported")


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
            port=app_config.PORT,
            url_path="/webhook",
            secret_token=app_config.SECRET_KEY,
            webhook_url=f"https://{app_config.DOMAIN}/webhook",
        )
    else:
        application.run_polling()
