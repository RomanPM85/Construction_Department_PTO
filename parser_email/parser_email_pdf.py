#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

import imaplib
import email
import os
from dotenv import load_dotenv

# loading environment variables from a file .env
load_dotenv()
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
search_query = os.getenv('SEARCH_QUERY')

imap_server = 'imap.yandex.ru'
imap_port = 993

# Establishing a connection to the server
mail = imaplib.IMAP4_SSL(imap_server, imap_port)
mail.login(db_user, db_password)

# Selecting a folder
folder_name = 'inbox'
mail.select(folder_name)

# Determining the addressee and attachment format
file_extension = 'pdf'

# The path to save attachments
save_folder = input(f"enter the name of the folder to save")
download_path = os.path.join(os.getcwd(), save_folder)

# Creating a folder if it does not exist
if not os.path.exists(download_path):
    os.makedirs(download_path)

# Search for emails
_, search_data = mail.search(None, search_query)

# Getting a list of found email numbers
message_numbers = search_data[0].split()

# Iterating through the found emails
for msg_num in message_numbers:
    # Receiving a message
    _, msg_data = mail.fetch(msg_num, '(RFC822)')

    # Extracting data from a message
    msg = email.message_from_bytes(msg_data[0][1])
    date_str = msg['Date']
    date_tuple = email.utils.parsedate(date_str)
    date = f'{date_tuple[0]}-{date_tuple[1]:02d}-{date_tuple[2]:02d}'
    subject = email.header.decode_header(msg['Subject'])[0][0]
    if isinstance(subject, bytes):
        subject = subject.decode('utf-8')
    print(f'Downloading {subject} ({date})...')

    # Processing an attachment
    for part in msg.walk():
        if part.get_content_type() == f'application/{file_extension}':
            filename = part.get_filename()
            filename_bytes = email.header.decode_header(filename)[0][0]
            if isinstance(filename_bytes, bytes):
                filename_str = filename_bytes.decode('utf-8')
            else:
                filename_str = filename_bytes
            filepath = os.path.join(download_path, f'{date}_{filename_str}')

            # Saving an attachment
            if os.path.isfile(filepath):
                print(f'File {filepath} already exists')
            else:
                with open(filepath, 'wb') as f:
                    f.write(part.get_payload(decode=True))
                print(f'Successfully downloaded {filename_str}')

# Closing the connection
mail.close()
mail.logout()
