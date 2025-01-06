#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import imaplib
import email
import os

# Параметры подключения


mail_username = input(f"Введите свою почту =>:")
mail_password = input(f"Введите свой пароль =>:")


imap_server = 'imap.yandex.ru'
imap_port = 993

# Установка соединения с сервером
mail = imaplib.IMAP4_SSL(imap_server, imap_port)
mail.login(mail_username, mail_password)

# Выбор папки
folder_name = 'inbox'
mail.select(folder_name)

# Определение адресата и формата вложения
search_email = input(f"Введите email для скачивания =>:")
search_query = '(FROM "' + str(search_email) + '")'
# file_extension = 'DOCX'

# Путь для сохранения вложений
name_folder = str(search_email)
download_path = os.path.join(os.getcwd(), str(name_folder))

# Создание папки, если ее не существует
if not os.path.exists(download_path):
    os.makedirs(download_path)

# Поиск писем
_, search_data = mail.search(None, search_query)

# Получение списка номеров найденных писем
message_numbers = search_data[0].split()

# Итерация по найденным письмам
for msg_num in message_numbers:
    # Получение сообщения
    _, msg_data = mail.fetch(msg_num, '(RFC822)')

    # Извлечение данных из сообщения
    msg = email.message_from_bytes(msg_data[0][1])
    date_str = msg['Date']
    date_tuple = email.utils.parsedate(date_str)
    date = f'{date_tuple[0]}-{date_tuple[1]:02d}-{date_tuple[2]:02d}'
    subject = email.header.decode_header(msg['Subject'])[0][0]
    if isinstance(subject, bytes):
        subject = subject.decode('utf-8')
    print(f'Downloading {subject} ({date})...')

    # Обработка вложения
    for part in msg.walk():
        if part.get_content_disposition() == 'attachment':
            print(part.get_filename())

        if part.get_content_type() == f'application/{file_extension}':
            filename = part.get_filename()
            filename_bytes = email.header.decode_header(filename)[0][0]
            if isinstance(filename_bytes, bytes):
                filename_str = filename_bytes.decode('utf-8')
            else:
                filename_str = filename_bytes
            filepath = os.path.join(download_path, f'{date}_{filename_str}')

            # Сохранение вложения
            if os.path.isfile(filepath):
                print(f'File {filepath} already exists')
            else:
                with open(filepath, 'wb') as f:
                    f.write(part.get_payload(decode=True))
                print(f'Successfully downloaded {filename_str}')

# Закрытие соединения
mail.close()
mail.logout()
