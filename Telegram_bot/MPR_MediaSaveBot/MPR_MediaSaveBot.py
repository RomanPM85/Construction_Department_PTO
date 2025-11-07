import logging
import os
import datetime
from pathlib import Path
import asyncio
from collections import defaultdict

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ContextTypes, CallbackQueryHandler, ConversationHandler
)
from webdav3.client import Client
from config import (OBJECTS, WEBDAV_OPTIONS, TELEGRAM_BOT_TOKEN, BASE_REMOTE_FOLDER, ALLOWED_SUPERUSER_IDS,
                    GROUP_ID_TO_OBJECT, ALLOWED_USER_IDS)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

client = Client(WEBDAV_OPTIONS)

LOCAL_SAVE_DIR = Path(__file__).parent / 'downloads'
LOCAL_SAVE_DIR.mkdir(exist_ok=True)

# Состояния для ConversationHandler
SELECT_OBJECT, SELECT_ROOM_OPTION, INPUT_ROOM_NUMBER, WAIT_PHOTO = range(4)

# Хранилище данных пользователей
user_data = {}

# Буфер для сбора фото из альбомов
photo_album_buffer = defaultdict(list)
photo_album_timers = {}
ALBUM_TIMEOUT = 3  # секунды ожидания для сбора всех фото альбома


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id in ALLOWED_SUPERUSER_IDS and update.message.chat.type == 'private':
        keyboard = [[InlineKeyboardButton(obj["name"], callback_data=obj["callback_data"])] for obj in OBJECTS]
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

    logging.info(f"object_selected called with data: {query.data}")

    try:
        obj = query.data.split('_', 1)[1]
    except Exception as e:
        logging.error(f"Error parsing callback_data: {e}")
        await query.edit_message_text("Ошибка обработки выбора объекта.")
        return ConversationHandler.END

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
    """Обработка выбора опции помещения"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == 'room_yes':
        await query.edit_message_text("Введите номер помещения:")
        return INPUT_ROOM_NUMBER
    else:
        user_data[user_id]['room'] = None
        # Можно сразу отправить сообщение, что теперь можно отправлять фото
        await query.edit_message_text(
            "Вы можете отправлять фото для загрузки. Фото будут сохранены в папку с текущей датой."
        )
        return WAIT_PHOTO


async def input_room_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода номера помещения"""
    user_id = update.message.from_user.id
    room_number = update.message.text.strip()
    user_data[user_id]['room'] = room_number

    keyboard = [[InlineKeyboardButton("📷 Загрузить фото", callback_data='upload_photo')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"Номер помещения установлен: {room_number}\nНажмите кнопку для загрузки фото:",
        reply_markup=reply_markup
    )
    return WAIT_PHOTO


async def upload_photo_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатия кнопки загрузки фото"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Отправьте фото для загрузки (можно несколько):")
    return WAIT_PHOTO


async def photo_handler_private(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка фото в личных сообщениях"""
    user_id = update.message.from_user.id
    if user_id not in ALLOWED_SUPERUSER_IDS:
        return

    photos = update.message.photo
    if not photos:
        await update.message.reply_text("Пожалуйста, отправьте фото.")
        return WAIT_PHOTO

    media_group_id = update.message.media_group_id

    # Одиночное фото
    if not media_group_id:
        # Очистка старых буферов альбомов
        for mgid in list(photo_album_buffer.keys()):
            photo_album_buffer.pop(mgid, None)
            if mgid in photo_album_timers:
                photo_album_timers[mgid].cancel()
                photo_album_timers.pop(mgid, None)

        largest_photo = photos[-1]
        await process_single_photo(update, context, largest_photo)
        return WAIT_PHOTO

    # Фото из альбома
    largest_photo = photos[-1]
    photo_album_buffer[media_group_id].append(largest_photo)

    # Логирование для отладки
    logging.info(f"Добавлено фото в альбом {media_group_id}. Всего в буфере: {len(photo_album_buffer[media_group_id])}")

    # Запускаем таймер только если он ещё не запущен
    if media_group_id not in photo_album_timers:
        async def process_album():
            await asyncio.sleep(ALBUM_TIMEOUT)
            logging.info(f"Обработка альбома {media_group_id} с {len(photo_album_buffer[media_group_id])} фото")

            await process_album_photos(update, context, photo_album_buffer[media_group_id])

            # Очистка буфера и таймера
            photo_album_buffer.pop(media_group_id, None)
            photo_album_timers.pop(media_group_id, None)

        photo_album_timers[media_group_id] = asyncio.create_task(process_album())
        logging.info(f"Запущен таймер для альбома {media_group_id}")

    return WAIT_PHOTO


async def process_single_photo(update: Update, context: ContextTypes.DEFAULT_TYPE, photo):
    """Обработка одиночного фото"""
    user_id = update.message.from_user.id
    data = user_data.setdefault(user_id, {})

    # Загрузка фото
    uploaded_path = await upload_photo_to_cloud(context, photo, data)

    if uploaded_path:
        message_text = f"✅ Фото загружено:\n`{uploaded_path}`"
    else:
        message_text = "❌ Не удалось загрузить фото."

    keyboard = [
        [
            InlineKeyboardButton("📷 Загрузить ещё", callback_data='upload_more'),
            InlineKeyboardButton("✅ Завершить", callback_data='finish_upload')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        message_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def process_album_photos(update: Update, context: ContextTypes.DEFAULT_TYPE, photos):
    """Обработка альбома фото"""
    user_id = update.message.from_user.id
    data = user_data.setdefault(user_id, {})

    uploaded_count = 0
    failed_count = 0

    for photo in photos:
        uploaded_path = await upload_photo_to_cloud(context, photo, data)
        if uploaded_path:
            uploaded_count += 1
        else:
            failed_count += 1

    total_photos = len(photos)

    if uploaded_count > 0:
        message_text = f"✅ Загружено {uploaded_count} из {total_photos} фото"
        if failed_count > 0:
            message_text += f"\n❌ Не удалось загрузить: {failed_count}"
    else:
        message_text = "❌ Не удалось загрузить фото"

    keyboard = [
        [
            InlineKeyboardButton("📷 Загрузить ещё", callback_data='upload_more'),
            InlineKeyboardButton("✅ Завершить", callback_data='finish_upload')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(message_text, reply_markup=reply_markup)


async def upload_photo_to_cloud(context: ContextTypes.DEFAULT_TYPE, photo, user_data_dict):
    """Загрузка фото на облако"""
    try:
        file_id = photo.file_id
        new_file = await context.bot.get_file(file_id)

        # Генерация уникального имени файла
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        file_name = f"photo_{timestamp}_{file_id[-8:]}.jpg"
        file_path = LOCAL_SAVE_DIR / file_name

        await new_file.download_to_drive(str(file_path))

        # Определение папки для загрузки
        room = user_data_dict.get('room')
        obj = user_data_dict.get('object', 'Без_объекта')
        today_str = datetime.datetime.now().strftime('%Y-%m-%d')

        if room:
            remote_folder = f"{BASE_REMOTE_FOLDER}/{obj}/{room}"
        else:
            remote_folder = f"{BASE_REMOTE_FOLDER}/{obj}/{today_str}"
            # remote_folder = f"{BASE_REMOTE_FOLDER}/{today_str}"

        remote_path = f"{remote_folder}/{file_name}"

        # Создание папки если не существует
        if not client.check(remote_folder):
            client.mkdir(remote_folder)

        # Загрузка на облако
        client.upload_sync(remote_path, str(file_path))

        # Удаление локального файла
        if file_path.exists():
            os.remove(file_path)

        return remote_path

    except Exception as e:
        logging.error(f"Ошибка при загрузке файла: {e}")
        return None


async def upload_more_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопки 'Загрузить ещё'"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Отправьте фото для загрузки (можно несколько):")
    return WAIT_PHOTO


async def finish_upload_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка кнопки 'Завершить'"""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    # Очистка данных пользователя
    if user_id in user_data:
        user_data.pop(user_id)

    keyboard = [[InlineKeyboardButton("🔄 Начать заново", callback_data='restart')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        "✅ Загрузка завершена!",
        reply_markup=reply_markup
    )
    return ConversationHandler.END


async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if user_id in user_data:
        user_data.pop(user_id)

    keyboard = [[InlineKeyboardButton(obj["name"], callback_data=obj["callback_data"])] for obj in OBJECTS]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "Выберите объект:",
        reply_markup=reply_markup
    )
    return SELECT_OBJECT


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена операции"""
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END


async def photo_handler_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.photo:
        return

    chat_id = update.message.chat_id  # ID группы
    user_id = update.message.from_user.id

    # Проверка разрешённых пользователей для группы
    allowed_users = ALLOWED_USER_IDS.get(chat_id, set())
    if user_id not in allowed_users:
        logging.warning(f"Пользователь {user_id} не разрешён в группе {chat_id}, пропуск загрузки.")
        return

    obj = GROUP_ID_TO_OBJECT.get(chat_id)
    if not obj:
        logging.warning(f"Неизвестный ID группы {chat_id}, пропуск загрузки.")
        return

    photo = update.message.photo[-1]
    file_id = photo.file_id
    new_file = await context.bot.get_file(file_id)

    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    file_name = f"{user_id}_photo_{timestamp}_{file_id[-8:]}.jpg"
    file_path = LOCAL_SAVE_DIR / file_name

    await new_file.download_to_drive(str(file_path))

    today_str = datetime.datetime.now().strftime('%Y-%m-%d')
    remote_folder = f"{BASE_REMOTE_FOLDER}/{obj}/{today_str}"
    remote_path = f"{remote_folder}/{file_name}"

    try:
        if not client.check(remote_folder):
            client.mkdir(remote_folder)

        client.upload_sync(remote_path, str(file_path))

        if file_path.exists():
            os.remove(file_path)

        logging.info(f"Фото из группы загружено: {remote_path}")

    except Exception as e:
        logging.error(f"Ошибка при загрузке файла в группе: {e}")


if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SELECT_OBJECT: [
                CallbackQueryHandler(object_selected, pattern=r'^object_')
            ],
            SELECT_ROOM_OPTION: [
                CallbackQueryHandler(room_option_selected, pattern=r'^room_')
            ],
            INPUT_ROOM_NUMBER: [
                MessageHandler(filters.TEXT & filters.ChatType.PRIVATE, input_room_number)
            ],
            WAIT_PHOTO: [
                MessageHandler(filters.PHOTO & filters.ChatType.PRIVATE, photo_handler_private),
                CallbackQueryHandler(upload_photo_button, pattern='^upload_photo$'),
                CallbackQueryHandler(upload_more_callback, pattern='^upload_more$'),
                CallbackQueryHandler(finish_upload_callback, pattern='^finish_upload$')
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        allow_reentry=True
    )

    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(restart, pattern='^restart$'))

    # Обработчик фото в группах
    application.add_handler(
        MessageHandler(
            filters.PHOTO & (filters.ChatType.GROUP | filters.ChatType.SUPERGROUP),
            photo_handler_group
        )
    )

    print("Бот запущен...")
    application.run_polling()
