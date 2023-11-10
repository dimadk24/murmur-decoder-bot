from settings import app_config

from io import BytesIO
import openai
from pathlib import Path

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
)

openai_client = openai.Client(api_key=app_config.OPEN_AI_API_KEY)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Welcome! Send me your voice messages in any language",
    )


async def message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.voice:
        file_id = update.message.voice.file_id
        tg_file = await context.bot.get_file(file_id)

        memory_file = BytesIO()
        await tg_file.download_to_memory(memory_file)
        memory_file.name = Path(tg_file.file_path).name

        transcript = openai_client.audio.transcriptions.create(
            model="whisper-1", file=memory_file
        )

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=transcript.text,
            reply_to_message_id=update.message.id,
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="I don't reply to texts, please send me a cute voice sample instead",
        )


# TODO:
# https://github.com/python-telegram-bot/python-telegram-bot/wiki/Exceptions%2C-Warnings-and-Logging

if __name__ == "__main__":
    application = (
        ApplicationBuilder().token(app_config.TELEGRAM_BOT_TOKEN).build()
    )

    start_handler = CommandHandler("start", start)
    application.add_handler(start_handler)
    message_handler = MessageHandler(None, message)
    application.add_handler(message_handler)

    if app_config.IS_LOCAL:
        application.run_polling()
    else:
        application.run_webhook(
            listen="0.0.0.0",
            port=3000,
            url_path="/webhook",
            secret_token=app_config.SECRET_KEY,
            webhook_url=f"https://{app_config.DOMAIN}/webhook",
        )
