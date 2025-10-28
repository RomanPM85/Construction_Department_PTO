import asyncio
from datetime import datetime, time, timedelta
import pytz
import sqlite3
import io
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CallbackQueryHandler, \
    ConversationHandler, CommandHandler
from telegram.error import BadRequest, TelegramError
from openpyxl import Workbook
from config import TOKEN, GROUPS, ALLOWED_USERS

moscow_tz = pytz.timezone("Europe/Moscow")

conn = sqlite3.connect("reports.db", check_same_thread=False)
cursor = conn.cursor()

# Создаем таблицу для хранения отчетов, если она не существует
cursor.execute("""
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    user_id INTEGER,
    response TEXT,
    report_type TEXT,
    company TEXT,
    group_id INTEGER
)
""")

# Таблица для отслеживания отправленных сообщений
cursor.execute("""
CREATE TABLE IF NOT EXISTS sent_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    user_id INTEGER,
    group_id INTEGER,
    message_type TEXT,
    sent_at TIMESTAMP
)
""")

# Создаём таблицу для пользователей групп
cursor.execute("""
CREATE TABLE IF NOT EXISTS group_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER,
    user_id INTEGER,
    user_name TEXT,
    first_name TEXT,
    last_name TEXT,
    UNIQUE(group_id, user_id)
)
""")


# Создаём таблицу для хранения отправленных уведомлений
cursor.execute("""
CREATE TABLE IF NOT EXISTS sent_notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    notification_type TEXT
)
""")

conn.commit()

# Состояние для ConversationHandler — ожидание отчета
WAITING_FOR_REPORT = 1

# Словарь для хранения контекста ожидания отчета от пользователей
waiting_for_report = {}


async def send_report_request_with_buttons(app, group_id, report_type):
    today_str = datetime.now(moscow_tz).strftime("%Y-%m-%d")
    users = GROUPS[group_id]

    pending_users = []
    for user_id, user_data in users.items():
        # Проверяем, что пользователь в группе
        try:
            member = await app.bot.get_chat_member(chat_id=group_id, user_id=user_id)
            if member.status in ['left', 'kicked']:
                continue  # Пользователь не в группе — пропускаем
        except Exception as e:
            print(f"Ошибка проверки участника {user_id} в группе {group_id}: {e}")
            continue  # При ошибке тоже пропускаем

        cursor.execute("""
        SELECT COUNT(*) FROM reports
        WHERE date=? AND user_id=? AND report_type=? AND group_id=?
        """, (today_str, user_id, report_type, group_id))
        sent = cursor.fetchone()[0] > 0
        if not sent:
            pending_users.append((user_id, user_data["name"]))

    if report_type == "morning":
        header = "☀️ *Напоминание!*\nПожалуйста, пришлите утренний отчёт о количестве людей на объекте:\n"
    else:
        header = "🌙 *Напоминание!*\nПожалуйста, пришлите вечерний отчёт о выполненных работах:\n"

    if not pending_users:
        text = header + "\nВсе отчёты получены. Спасибо!"
        await app.bot.send_message(chat_id=group_id, text=text, parse_mode=ParseMode.MARKDOWN)
        return

    buttons = []
    text_lines = [header]
    for user_id, name in pending_users:
        text_lines.append(f"• {name}")
        buttons.append([InlineKeyboardButton(f"📝 Отправить отчёт ({name})",
                                             callback_data=f"report_{report_type}_{user_id}_{group_id}")])

    text = "\n".join(text_lines)
    reply_markup = InlineKeyboardMarkup(buttons)

    await app.bot.send_message(
        chat_id=group_id,
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=reply_markup
    )


async def send_evening_summary_21(app, group_id):
    today_str = datetime.now(moscow_tz).strftime("%Y-%m-%d")
    users = GROUPS[group_id]

    evening_sent = []
    evening_pending = []

    for user_id, user_data in users.items():
        # Проверяем, что пользователь в группе
        try:
            member = await app.bot.get_chat_member(chat_id=group_id, user_id=user_id)
            if member.status in ['left', 'kicked']:
                continue  # Пользователь не в группе — пропускаем
        except Exception as e:
            print(f"Ошибка проверки участника {user_id} в группе {group_id}: {e}")
            continue

        cursor.execute("""
        SELECT COUNT(*) FROM reports
        WHERE date=? AND user_id=? AND report_type='evening' AND group_id=?
        """, (today_str, user_id, group_id))
        if cursor.fetchone()[0] > 0:
            evening_sent.append(user_data["name"])
        else:
            evening_pending.append(user_data["name"])

    text = "🕘 *Сводка по отчётам за сегодня:*\n\n"

    text += "🌙 *Вечерний отчёт:*\n"
    if evening_sent:
        text += "✅ Отправили:\n" + ("\n".join(f"• {n}" for n in evening_sent)) + "\n"
    else:
        text += "✅ Отправили:\n• Никто\n"
    if evening_pending:
        text += "⚠️ Не отправили:\n" + ("\n".join(f"• {n}" for n in evening_pending)) + "\n"

    await app.bot.send_message(
        chat_id=group_id,
        text=text,
        parse_mode=ParseMode.MARKDOWN
    )


async def schedule_tasks(app):
    sent_10 = set()
    sent_19 = set()
    sent_21 = set()

    while True:
        now = datetime.now(moscow_tz)
        current_time = now.time()
        today_str = now.strftime("%Y-%m-%d")
        group_ids = GROUPS.keys()

        # Проверяем в базе, отправлялось ли сообщение 9:30 сегодня
        cursor.execute("""
        SELECT COUNT(*) FROM sent_notifications
        WHERE date=? AND notification_type='sent_930'
        """, (today_str,))
        sent_930_sent = cursor.fetchone()[0] > 0

        if current_time >= time(9, 30) and not sent_930_sent:
            warning_message = (
                "ВНИМАНИЕ!!! Все руководители!!! Срочно направьте информацию Амзе о количестве людей на площадке!!!\n"
                "За непредоставление — штраф 3.000 руб.!!!"
            )
            for group_id in group_ids:
                try:
                    await app.bot.send_message(chat_id=group_id, text=warning_message)
                except Exception as e:
                    print(f"Ошибка при отправке сообщения в группу {group_id}: {e}")

            # Записываем факт отправки в базу
            cursor.execute("""
            INSERT INTO sent_notifications (date, notification_type) VALUES (?, ?)
            """, (today_str, 'sent_930'))
            conn.commit()

        for group_id in group_ids:
            # if current_time >= time(10, 0) and group_id not in sent_10:
            #     await send_report_request_with_buttons(app, group_id, "morning")
            #     sent_10.add(group_id)

            if current_time >= time(19, 0) and group_id not in sent_19:
                await send_report_request_with_buttons(app, group_id, "evening")
                sent_19.add(group_id)

            if current_time >= time(21, 0) and group_id not in sent_21:
                await send_evening_summary_21(app, group_id)
                sent_21.add(group_id)

        # Сброс флагов в полночь
        if current_time < time(0, 1):
            sent_10.clear()
            sent_19.clear()
            sent_21.clear()

        await asyncio.sleep(30)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    try:
        # Сначала проверяем данные, потом отвечаем на callback
        if not query.data.startswith("report_"):
            await query.answer("Неверный формат данных", show_alert=True)
            return

        parts = query.data.split("_")
        if len(parts) != 4:
            await query.answer("Неверный формат данных", show_alert=True)
            return

        report_type = parts[1]
        target_user_id = int(parts[2])
        group_id = int(parts[3])

        # Проверяем, что кнопку нажал тот пользователь, для которого она предназначена
        if query.from_user.id != target_user_id:
            await query.answer("Эта кнопка предназначена для другого пользователя!", show_alert=True)
            return

        # Проверяем, не отправлен ли уже отчет за сегодня
        today_str = datetime.now(moscow_tz).strftime("%Y-%m-%d")
        cursor.execute("""
        SELECT COUNT(*) FROM reports
        WHERE date=? AND user_id=? AND report_type=? AND group_id=?
        """, (today_str, target_user_id, report_type, group_id))
        if cursor.fetchone()[0] > 0:
            await query.answer("Вы уже отправили отчет за сегодня!", show_alert=True)
            return

        # Проверяем, не ожидается ли уже отчет от этого пользователя
        if target_user_id in waiting_for_report:
            await query.answer("Вы уже начали процесс отправки отчета. Проверьте личные сообщения!", show_alert=True)
            return

        # Сохраняем контекст ожидания отчёта
        waiting_for_report[target_user_id] = {
            "report_type": report_type,
            "group_id": group_id,
            "message_id": query.message.message_id,
            "timestamp": datetime.now(moscow_tz)
        }

        report_name = "утренний отчёт о количестве людей" if report_type == "morning" else "вечерний отчёт о выполненных работах"

        try:
            # Пытаемся отправить личное сообщение
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"Пожалуйста, отправьте {report_name}:"
            )
            await query.answer("Проверьте личные сообщения для отправки отчёта.", show_alert=True)

        except TelegramError as e:
            # Если не удалось отправить личное сообщение
            del waiting_for_report[target_user_id]  # Очищаем ожидание
            error_text = "Не удалось отправить вам личное сообщение. Пожалуйста, напишите боту в личные сообщения и попробуйте снова."

            try:
                await query.answer(error_text, show_alert=True)
            except BadRequest:
                # Если не удалось ответить на callback, отправляем сообщение в группу
                await context.bot.send_message(
                    chat_id=group_id,
                    text=f"@{query.from_user.username}, {error_text}"
                )

    except BadRequest as e:
        if "Query is too old" in str(e):
            # Если callback устарел, отправляем новое сообщение
            try:
                await context.bot.send_message(
                    chat_id=group_id,
                    text="⚠️ Это сообщение устарело. Пожалуйста, используйте актуальные кнопки для отправки отчета."
                )
            except TelegramError:
                pass  # Игнорируем ошибки при отправке сообщения об устаревшем callback

    except Exception as e:
        # Логируем неожиданные ошибки
        print(f"Unexpected error in button_handler: {e}")
        try:
            await query.answer("Произошла ошибка. Пожалуйста, попробуйте позже.", show_alert=True)
        except TelegramError:
            pass

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    try:
        if update.effective_message:
            chat_id = update.effective_message.chat_id
        else:
            return

        error_message = f"Произошла ошибка: {context.error}"

        if isinstance(context.error, BadRequest):
            if "Query is too old" in str(context.error):
                error_message = "Это сообщение устарело. Пожалуйста, используйте актуальные кнопки."

        await context.bot.send_message(
            chat_id=chat_id,
            text=error_message
        )

    except Exception as e:
        print(f"Error in error_handler: {e}")

async def handle_private_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    # Проверяем, ожидаем ли отчёт от этого пользователя
    if user_id in waiting_for_report:
        report_info = waiting_for_report[user_id]
        report_type = report_info["report_type"]
        group_id = report_info["group_id"]

        # Проверяем время ожидания (таймаут 5 минут)
        if datetime.now(moscow_tz) - report_info["timestamp"] > timedelta(minutes=5):
            del waiting_for_report[user_id]
            await update.message.reply_text(
                "Время ожидания отчёта истекло. Пожалуйста, нажмите кнопку отправки отчёта в группе снова."
            )
            return

        today_str = datetime.now(moscow_tz).strftime("%Y-%m-%d")

        # Проверяем еще раз, не был ли отчет уже отправлен
        cursor.execute("""
        SELECT COUNT(*) FROM reports
        WHERE date=? AND user_id=? AND report_type=? AND group_id=?
        """, (today_str, user_id, report_type, group_id))
        if cursor.fetchone()[0] > 0:
            del waiting_for_report[user_id]
            await update.message.reply_text(
                "Вы уже отправили отчет за сегодня!"
            )
            return

        text = update.message.text

        # Сохраняем отчёт в базу данных
        cursor.execute("""
        INSERT INTO reports (date, user_id, response, report_type, company, group_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (today_str, user_id, text, report_type, GROUPS[group_id][user_id]["company"], group_id))
        conn.commit()

        # Отправляем подтверждение пользователю
        await update.message.reply_text("✅ Спасибо! Ваш отчёт принят.")

        # Формируем сообщение с отчётом для группы
        user_name = GROUPS[group_id][user_id]["name"]
        company = GROUPS[group_id][user_id]["company"]
        report_title = "Утренний отчёт" if report_type == "morning" else "Вечерний отчёт"

        group_message = f"""
📋 *{report_title}*
👤 *Сотрудник:* [{user_name}](tg://user?id={user_id})
🏢 *Компания:* {company}
📅 *Дата:* {today_str}

*Отчёт:*
{text}
"""

        await context.bot.send_message(
            chat_id=group_id,
            text=group_message,
            parse_mode=ParseMode.MARKDOWN
        )

        # Удаляем пользователя из списка ожидающих отчёт
        del waiting_for_report[user_id]
    else:
        # Если отчёт не ожидается, проверяем, зарегистрирован ли пользователь в группах
        user_groups = [gid for gid, users in GROUPS.items() if user_id in users]
        if user_groups:
            await update.message.reply_text(
                "Для отправки отчёта используйте кнопку в групповом чате."
            )

async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    group_id = message.chat.id
    user = message.from_user

    if user.is_bot:
        return

    try:
        cursor.execute("""
            INSERT OR IGNORE INTO group_users (group_id, user_id, user_name, first_name, last_name)
            VALUES (?, ?, ?, ?, ?)
        """, (
            group_id,
            user.id,
            user.username or '',
            user.first_name or '',
            user.last_name or ''
        ))
        conn.commit()
    except Exception as e:
        print(f"Ошибка при сохранении пользователя {user.id} в группу {group_id}: {e}")

async def post_init(application):
    """Запускаем фоновые задачи после инициализации приложения"""
    asyncio.create_task(schedule_tasks(application))

async def get_reports_xlsx(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in ALLOWED_USERS:
        await update.message.reply_text("У вас нет прав на выполнение этой команды.")
        return

    if update.effective_chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("Команду нужно вызывать из группы.")
        return

    group_id = update.effective_chat.id

    args = context.args
    if len(args) != 1:
        await update.message.reply_text("Использование: /get_reports_xlsx <morning|evening>")
        return

    report_type = args[0].lower()
    if report_type not in ['morning', 'evening']:
        await update.message.reply_text("Тип отчёта должен быть 'morning' или 'evening'.")
        return

    cursor.execute("""
    SELECT date, user_id, response, company FROM reports
    WHERE group_id=? AND report_type=?
    ORDER BY date ASC
    """, (group_id, report_type))

    rows = cursor.fetchall()

    if not rows:
        await update.message.reply_text("Отчёты не найдены.")
        return

    users = GROUPS.get(group_id, {})

    wb = Workbook()
    ws = wb.active
    ws.title = "Reports"

    ws.append(["Дата", "Сотрудник", "User ID", "Компания", "Отчёт"])

    for date_str, user_id_report, response, company in rows:
        user_name = users.get(user_id_report, {}).get("name", f"User {user_id_report}")
        ws.append([date_str, user_name, user_id_report, company, response])

    file_stream = io.BytesIO()
    wb.save(file_stream)
    file_stream.seek(0)

    filename = f"reports_{report_type}_{group_id}.xlsx"

    # Отправляем файл в ЛС пользователю, вызвавшему команду
    try:
        await context.bot.send_document(
            chat_id=user_id,
            document=InputFile(file_stream, filename=filename),
            caption=f"Отчёты: {report_type} за весь период"
        )
        await update.message.reply_text("Отчёт отправлен вам в личные сообщения.")
    except Exception as e:
        await update.message.reply_text(
            "Не удалось отправить файл в личные сообщения. "
            "Пожалуйста, начните чат с ботом и попробуйте снова."
        )

async def get_group_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ALLOWED_USERS:
        await update.message.reply_text("У вас нет прав на выполнение этой команды.")
        return

    if update.effective_chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("Команду нужно вызывать из группы.")
        return

    group_id = update.effective_chat.id

    cursor.execute("""
        SELECT user_id, user_name, first_name, last_name FROM group_users
        WHERE group_id=?
        ORDER BY first_name ASC
    """, (group_id,))

    rows = cursor.fetchall()
    if not rows:
        await update.message.reply_text("Пользователи в группе не найдены.")
        return

    lines = []
    for uid, username, first_name, last_name in rows:
        name_display = username if username else f"{first_name} {last_name}".strip()
        lines.append(f"• {name_display} (ID: {uid})")

    text = "Список пользователей в группе:\n" + "\n".join(lines)

    try:
        await context.bot.send_message(chat_id=user_id, text=text)
        await update.message.reply_text("Список пользователей отправлен вам в личные сообщения.")
    except Exception as e:
        print(f"Ошибка при отправке списка пользователей в ЛС: {e}")
        await update.message.reply_text(
            "Не удалось отправить вам сообщение в личные сообщения. "
            "Пожалуйста, начните чат с ботом и попробуйте снова."
        )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in ALLOWED_USERS:
        await update.message.reply_text("У вас нет прав на выполнение этой команды.")
        return

    help_text = (
        "Доступные команды:\n"
        "/get_reports_xlsx <morning|evening> — выгрузить отчёты в Excel\n"
        "/get_group_users — получить список пользователей группы\n"
        "/help — показать это сообщение"
    )
    await update.message.reply_text(help_text)


def main():
    try:
        app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()

        # Обработчик нажатий кнопок
        app.add_handler(CallbackQueryHandler(button_handler))

        # Обработчик личных сообщений
        app.add_handler(MessageHandler(
            filters.TEXT & filters.ChatType.PRIVATE & (~filters.COMMAND),
            handle_private_message
        ))

        # Обработчик сообщений в группах
        app.add_handler(MessageHandler(
            filters.TEXT & filters.ChatType.GROUPS & (~filters.COMMAND),
            handle_group_message
        ))

        # Обработчик команды в инициализацию бота для выгрузки отчета
        app.add_handler(CommandHandler("get_reports_xlsx", get_reports_xlsx))

        # Обработчик команды в инициализацию бота для выгрузки пользователей
        app.add_handler(CommandHandler("get_group_users", get_group_users))

        # Обработчик команды для вызова доступных команд
        app.add_handler(CommandHandler("help", help_command))

        # Добавляем обработчик ошибок
        app.add_error_handler(error_handler)

        print("Бот запущен и работает...")
        app.run_polling()

    except Exception as e:
        print(f"Critical error: {e}")
        # Можно добавить логирование или отправку уведомления администратору


if __name__ == "__main__":
    main()
