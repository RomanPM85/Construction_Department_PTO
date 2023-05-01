#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
# Источник
# https://www.dmosk.ru/instruktions.php?object=python-mail&ysclid=laekvbc8ip119718153
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from platform import python_version
import config

server = 'smtp.mail.ru'
user = config.user  # логин отправителя
password = config.password  # пароль отправителя

# recipients = ['recipients1@email.ru', 'recipients2@email.ru']
recipients = config.recipients  # отправитель
sender = config.sender  # получатель
subject = 'Тема письма'  # Тема письма
text = 'текст письма'  # текст письма
html = '<html><head></head><body><p>' + text + '</p></body></html>'

filepath = config.filepath  # путь к файлу
basename = os.path.basename(filepath)
filesize = os.path.getsize(filepath)

msg = MIMEMultipart('alternative')
msg['Subject'] = subject
# msg['From'] = 'Python script <' + sender + '>'
msg['From'] = 'sender@email.ru<' + sender + '>'
msg['To'] = ', '.join(recipients)
msg['Reply-To'] = sender
msg['Return-Path'] = sender
msg['X-Mailer'] = 'Python/' + (python_version())

part_text = MIMEText(text, 'plain')
part_html = MIMEText(html, 'html')
part_file = MIMEBase('application', 'octet-stream; name="{}"'.format(basename))
part_file.set_payload(open(filepath, "rb").read())
part_file.add_header('Content-Description', basename)
part_file.add_header('Content-Disposition', 'attachment; filename="{}"; size={}'.format(basename, filesize))
encoders.encode_base64(part_file)

msg.attach(part_text)
msg.attach(part_html)
msg.attach(part_file)

mail = smtplib.SMTP_SSL(server)
mail.login(user, password)
mail.sendmail(sender, recipients, msg.as_string())
mail.quit()
