import logging
import os
import datetime
from pathlib import Path
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ContextTypes, CallbackQueryHandler, ConversationHandler
)
from webdav3.client import Client
from config import WEBDAV_OPTIONS, TELEGRAM_BOT_TOKEN, BASE_REMOTE_FOLDER, ALLOWED_SUPERUSER_IDS

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

client = Client(WEBDAV_OPTIONS)

LOCAL_SAVE_DIR = Path(__file__).parent / 'downloads'
LOCAL_SAVE_DIR.mkdir(exist_ok=True)

# Состояния разговора для суперпользователя в личке
SELECT_OBJECT, SELECT_ROOM_OPTION, INPUT_ROOM_NUMBER, WAIT_PHOTO = range(4)
user_data = {}

# --- Логика для личных сообщений суперпользователя ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in ALLOWED_SUPERUSER_IDS and update.message.chat.type == 'private':
        keyboard = [
            [InlineKeyboardButton("ФОК", callback_data='object_FOK')],
            [InlineKeyboardButton("МДЦ", callback_data='object_MDC')],
            [InlineKeyboardButton("ГрШК21", callback_data='object_GrShK21')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Выберите объект:",
            reply_markup=reply_markup
        )
        return SELECT_OBJECT
    else:
        await update.message.reply_text("Привет! Пришлите фото в группу или лично — я загружу его на облако.")
        return ConversationHandler.END

async def object_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    obj = query.data.split('_')[1]
    user_data[query.from_user.id] = {'object': obj}

    keyboard = [
        [InlineKeyboardButton("Указать помещение", callback_data='room_yes')],
        [InlineKeyboardButton("Не указывать", callback_data='room_no')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        text=f"Выбран объект: {obj}\nВыберите опцию:",
        reply_markup=reply_markup
    )
    return SELECT_ROOM_OPTION

async def room_option_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == 'room_yes':
        await query.edit_message_text("Введите номер помещения:")
        return INPUT_ROOM_NUMBER
    else:
        user_data[user_id]['room'] = None
        await query.edit_message_text("Отправьте фото для загрузки.")
        return WAIT_PHOTO

async def input_room_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    room_number = update.message.text.strip()
    user_data[user_id]['room'] = room_number
    await update.message.reply_text(f"Номер помещения установлен: {room_number}\nОтправьте фото для загрузки.")
    return WAIT_PHOTO

async def photo_handler_private(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in ALLOWED_SUPERUSER_IDS:
        return

    photos = update.message.photo
    if not photos:
        await update.message.reply_text("Пожалуйста, отправьте фото.")
        return WAIT_PHOTO

    data = user_data.get(user_id, {})
    room = data.get('room')
    obj = data.get('object', 'Без_объекта')

    today_str = datetime.datetime.now().strftime('%Y-%m-%d')

    if room:
        remote_folder = f"{BASE_REMOTE_FOLDER}/{room}"
    else:
        remote_folder = f"{BASE_REMOTE_FOLDER}/{obj}/{today_str}"

    uploaded_files = []

    for photo in photos:
        file_id = photo.file_id
        new_file = await context.bot.get_file(file_id)

        file_path = LOCAL_SAVE_DIR / f"{file_id}.jpg"
        await new_file.download_to_drive(str(file_path))

        remote_path = f"{remote_folder}/{file_path.name}"

        try:
            if not client.check(remote_folder):
                client.mkdir(remote_folder)

            client.upload_sync(remote_path, str(file_path))

            if file_path.exists():
                os.remove(file_path)

            uploaded_files.append(remote_path)

        except Exception as e:
            logging.error(f"Ошибка при загрузке файла {file_path.name}: {e}")
            # Можно собрать ошибки в список, если нужно

    if uploaded_files:
        files_list_str = '\n'.join(uploaded_files)
        message_text = f"Успешно загружены файлы:\n{files_list_str}"
    else:
        message_text = "Не удалось загрузить ни одного фото."

    keyboard = [
        [InlineKeyboardButton("Завершить загрузку", callback_data='finish_upload')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Отправляем одно сообщение с результатом и кнопкой
    await update.message.reply_text(message_text + "\n\nОтправьте ещё фото или завершите загрузку:", reply_markup=reply_markup)

    return WAIT_PHOTO

async def wait_photo_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == 'finish_upload':
        user_data.pop(user_id, None)
        await query.edit_message_text("Загрузка завершена.")
        return ConversationHandler.END

async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [
        [InlineKeyboardButton("ФОК", callback_data='object_FOK')],
        [InlineKeyboardButton("МДЦ", callback_data='object_MDC')],
        [InlineKeyboardButton("ГрШК21", callback_data='object_GrShK21')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "Выберите объект:",
        reply_markup=reply_markup
    )
    return SELECT_OBJECT

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END

# --- Логика для групп и супергрупп ---

async def photo_handler_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.photo:
        return

    photo = update.message.photo[-1]
    file_id = photo.file_id
    new_file = await context.bot.get_file(file_id)

    file_path = LOCAL_SAVE_DIR / f"{file_id}.jpg"
    await new_file.download_to_drive(str(file_path))

    today_str = datetime.datetime.now().strftime('%Y-%m-%d')
    remote_folder = f"{BASE_REMOTE_FOLDER}/{today_str}"
    remote_path = f"{remote_folder}/{file_path.name}"

    try:
        if not client.check(remote_folder):
            client.mkdir(remote_folder)

        client.upload_sync(remote_path, str(file_path))

        if file_path.exists():
            os.remove(file_path)

        # Можно не отвечать в группе, чтобы не спамить
        # await update.message.reply_text("Фото успешно загружено.")

    except Exception as e:
        logging.error(f"Ошибка при загрузке файла в группе: {e}")

if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECT_OBJECT: [CallbackQueryHandler(object_selected, pattern=r'^object_')],
            SELECT_ROOM_OPTION: [CallbackQueryHandler(room_option_selected, pattern=r'^room_')],
            INPUT_ROOM_NUMBER: [MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, input_room_number)],
            WAIT_PHOTO: [
                MessageHandler(filters.PHOTO & filters.ChatType.PRIVATE, photo_handler_private),
                CallbackQueryHandler(wait_photo_callback, pattern='^finish_upload$')
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    )

    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(restart, pattern='^restart$'))

    # Обработчик фото в группах и супергруппах
    application.add_handler(
        MessageHandler(
            filters.PHOTO & (filters.ChatType.GROUP | filters.ChatType.SUPERGROUP),
            photo_handler_group
        )
    )

    print("Бот запущен...")
    application.run_polling()
