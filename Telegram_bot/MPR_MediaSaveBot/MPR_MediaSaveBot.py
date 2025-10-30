import logging
import os
import datetime
from pathlib import Path
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from webdav3.client import Client
from config import WEBDAV_OPTIONS, TELEGRAM_BOT_TOKEN, BASE_REMOTE_FOLDER, FOLDERS_TO_CHECK, ALLOWED_USER_IDS


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

client = Client(WEBDAV_OPTIONS)

LOCAL_SAVE_DIR = Path(__file__).parent / 'downloads'
LOCAL_SAVE_DIR.mkdir(exist_ok=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Пришли фото в группу или лично — я загружу его на облако.")

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.photo:
        return

    user_id = update.message.from_user.id
    if user_id not in ALLOWED_USER_IDS:
        return

    photo = update.message.photo[-1]
    file_id = photo.file_id
    new_file = await context.bot.get_file(file_id)

    file_path = LOCAL_SAVE_DIR / f"{file_id}.jpg"
    await new_file.download_to_drive(str(file_path))

    today_str = datetime.datetime.now().strftime('%Y-%m-%d')
    dated_remote_folder = f"{BASE_REMOTE_FOLDER}/{today_str}"
    remote_path = f"{dated_remote_folder}/{file_path.name}"

    try:
        folders_to_check = FOLDERS_TO_CHECK + [dated_remote_folder]

        for folder in folders_to_check:
            if not client.check(folder):
                client.mkdir(folder)

        client.upload_sync(remote_path, str(file_path))

        try:
            if file_path.exists():
                os.remove(file_path)
        except Exception as remove_error:
            logging.warning(f"Ошибка при удалении файла {file_path}: {remove_error}")

        # Отправляем сообщение только в личных чатах
        chat_type = update.message.chat.type
        if chat_type == 'private':
            await update.message.reply_text(f"Фото успешно загружено как {remote_path}")

    except Exception as e:
        await update.message.reply_text(f"Ошибка при загрузке файла: {e}")


if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))

    application.add_handler(
        MessageHandler(
            filters.PHOTO & (filters.ChatType.PRIVATE | filters.ChatType.GROUP | filters.ChatType.SUPERGROUP),
            photo_handler
        )
    )

    print("Бот запущен...")
    application.run_polling()
