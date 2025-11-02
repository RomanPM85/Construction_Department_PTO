# config.py

TELEGRAM_BOT_TOKEN = "TOKEN"
MAILRU_EMAIL = "email@gmail.com"
NAME_PASS_CLOUD_MAIL_APP = "NameBot"
MAILRU_PASSWORD = "PASSWORD"

WEBDAV_OPTIONS = {
    'webdav_hostname': "https://webdav.cloud.mail.ru",
    'webdav_login': "email@gmail.com",      # замените на ваш логин
    'webdav_password': "appPassWord",        # замените на ваш пароль
}
# Основная папка для загрузки
BASE_REMOTE_FOLDER = '/folder/Foto_folder'

# Список папок для проверки и создания (включая BASE_REMOTE_FOLDER и родительские)
FOLDERS_TO_CHECK = [
    '/folder',
    '/folder/Foto_folder',
    BASE_REMOTE_FOLDER,
]

# Список разрешённых пользователей (замените на реальные user_id)
ALLOWED_USER_IDS = {1234567890, 1234567891}
ALLOWED_SUPERUSER_IDS = [1234567890]

OBJECTS = [
    {"name": "obj1", "callback_data": "object_obj1"},
    {"name": "obj2", "callback_data": "object_obj2"},
    {"name": "obj3", "callback_data": "object_obj3"},
]
