#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import smtplib
import csv
import pandas as pd
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from platform import python_version
from pathlib import Path


def sends_messages(name_task, final, recipients, copy_recipients):
    """
    Функция для отправки сообщений
    """
    server = 'smtp.yandex.ru'
    user = 'your_email'
    password = 'your_password'
    sender = 'r.mamchiy@ingacademy.ru'
    subject = f'{name_task}'

    text = f'{name_task} '
    text_final = f'Дата выдачи {final}'
    signature = 'С уважением ООО "'
    html = ('<html><head></head><body><h3>Доброго дня!</h3><p>Напоминаем о сроке выдачи следующего документа:</p>'
            '<h4>' + text + '</h4><p>' + text_final + '</p><p>' + signature + '</p> </body></html>')

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = 'Company " <' + sender + '>'
    msg['To'] = ', '.join(recipients)
    msg['CC'] = ', '.join(copy_recipients)
    msg['Reply-To'] = sender
    msg['Return-Path'] = sender
    msg['X-Mailer'] = 'Python/' + (python_version())

    part_text = MIMEText(text, 'plain')
    part_html = MIMEText(html, 'html')

    msg.attach(part_text)
    msg.attach(part_html)

    mail = smtplib.SMTP_SSL(server)
    mail.login(user, password)
    mail.sendmail(sender, recipients, msg.as_string())
    mail.quit()


def looking_projects(looking_date, looking_file):
    path_csv = Path.cwd() / looking_file
    with open(path_csv, 'r', encoding='utf-8-sig', newline='') as file:
        reader = csv.DictReader(file, delimiter=',')
        for row in reader:
            if row['message'] < looking_date:
                name_task = row['name-task']
                final = row['final']
                recipients = row['recipients'].split(",")
                copy_recipients = row['copy_recipients'].split(",")
                sends_messages(name_task, final, recipients, copy_recipients)
                print(name_task, final)
            else:
                pass


def convert_pd_xlsx_to_csv(file_xlsx, file_csv):
    path_file_xlsx = Path.cwd() / file_xlsx
    path_file_csv = Path.cwd() / file_csv
    read_file_xlsx = pd.read_excel(path_file_xlsx)
    read_file_xlsx.to_csv(path_file_csv, index=False, header=True)


if __name__ == "__main__":
    welcome = "Программа для отправки писем с сообщением о выдаче документов."
    print(welcome)

    start_programme = input(f'Для запуска программы введите Y\n=>')
    if start_programme == 'Y':
        try:
            FILE_XLSX = 'file.xlsx'
            FILE_CSV = 'file.csv'
            convert_pd_xlsx_to_csv(FILE_XLSX, FILE_CSV)
            today_date = date.today().strftime("%Y-%m-%d")
            current_date = str(today_date)
            looking_projects(current_date, FILE_CSV)
        except FileNotFoundError:
            print(f'Нет файла file.xlsx\n необходим файл в папке где запущена программа!')
        finally:
            print(f'Программа завершена!')
    else:
        pass
