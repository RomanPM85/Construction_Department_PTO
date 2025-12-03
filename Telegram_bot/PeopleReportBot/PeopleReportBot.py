import asyncio
from datetime import datetime, time, timedelta
import pytz
import sqlite3
import io
import config  # Импорт config с OPENING_DATE
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CallbackQueryHandler, CommandHandler
from telegram.error import BadRequest, TelegramError
from openpyxl import Workbook
from config import TOKEN, GROUPS, ALLOWED_USERS

moscow_tz = pytz.timezone("Europe/Moscow")

conn = sqlite3.connect("reports.db", check_same_thread=False)
cursor = conn.cursor()

# Создаем таблицы, если их нет
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

cursor.execute("""
CREATE TABLE IF NOT EXISTS sent_notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    notification_type TEXT
)
""")

conn.commit()

WAITING_FOR_REPORT = 1
waiting_for_report = {}

# --- Функция отправки запроса отчёта с кнопками ---

async def send_report_request_with_buttons(app, group_id, report_type):
    today_str = datetime.now(moscow_tz).strftime("%Y-%m-%d")
    users = GROUPS[group_id]

    pending_users = []
    for user_id, user_data in users.items():
        try:
            member = await app.bot.get_chat_member(chat_id=group_id, user_id=user_id)
            if member.status in ['left', 'kicked']:
                continue
        except Exception as e:
            print(f"Ошибка проверки участника {user_id} в группе {group_id}: {e}")
            continue

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

# --- Функция отправки вечерней сводки в 21:00 ---

async def send_evening_summary_21(app, group_id):
    today_str = datetime.now(moscow_tz).strftime("%Y-%m-%d")
    users = GROUPS[group_id]

    evening_sent = []
    evening_pending = []

    for user_id, user_data in users.items():
        try:
            member = await app.bot.get_chat_member(chat_id=group_id, user_id=user_id)
            if member.status in ['left', 'kicked']:
                continue
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

# --- функцию для отправки утреннего сообщения
async def send_morning_greeting(app, group_id):
    today = datetime.now(moscow_tz).date()
    opening_date = datetime.strptime(config.OPENING_DATE, "%Y-%m-%d").date()
    days_left = (opening_date - today).days

    if days_left < 0:
        message = "Объект уже открыт!"
    else:
        message = f"Доброе утро! До открытия объекта осталось дней: {days_left} !!!"

    try:
        await app.bot.send_message(chat_id=group_id, text=message)
    except Exception as e:
        print(f"Ошибка при отправке утреннего сообщения в группу {group_id}: {e}")

# --- Фоновая задача планировщика ---

async def schedule_tasks(app):
    sent_10 = set()
    sent_19 = set()
    sent_21 = set()
    sent_9 = set()  # для утреннего сообщения

    while True:
        now = datetime.now(moscow_tz)
        current_time = now.time()
        today_str = now.strftime("%Y-%m-%d")
        group_ids = GROUPS.keys()

        # Проверяем, отправляли ли уже утреннее сообщение сегодня
        cursor.execute("""
            SELECT COUNT(*) FROM sent_notifications WHERE date=? AND notification_type='morning_greeting'
        """, (today_str,))
        morning_sent = cursor.fetchone()[0] > 0

        if current_time >= time(9, 0) and not morning_sent:
            for group_id in group_ids:
                try:
                    await send_morning_greeting(app, group_id)
                except Exception as e:
                    print(f"Ошибка при отправке утреннего сообщения в группу {group_id}: {e}")

            cursor.execute("""
                INSERT INTO sent_notifications (date, notification_type) VALUES (?, ?)
            """, (today_str, 'morning_greeting'))
            conn.commit()

        cursor.execute("""
            SELECT COUNT(*) FROM sent_notifications WHERE date=? AND notification_type='sent_930'
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

        if current_time < time(0, 1):
            sent_10.clear()
            sent_19.clear()
            sent_21.clear()
            sent_9.clear()

        await asyncio.sleep(30)

# --- Обработчик нажатий кнопок ---

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    try:
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

        if query.from_user.id != target_user_id:
            await query.answer("Эта кнопка предназначена для другого пользователя!", show_alert=True)
            return

        today_str = datetime.now(moscow_tz).strftime("%Y-%m-%d")
        cursor.execute("""
        SELECT COUNT(*) FROM reports
        WHERE date=? AND user_id=? AND report_type=? AND group_id=?
        """, (today_str, target_user_id, report_type, group_id))
        if cursor.fetchone()[0] > 0:
            await query.answer("Вы уже отправили отчет за сегодня!", show_alert=True)
            return

        if target_user_id in waiting_for_report:
            await query.answer("Вы уже начали процесс отправки отчета. Проверьте личные сообщения!", show_alert=True)
            return

        waiting_for_report[target_user_id] = {
            "report_type": report_type,
            "group_id": group_id,
            "message_id": query.message.message_id,
            "timestamp": datetime.now(moscow_tz)
        }

        report_name = "утренний отчёт о количестве людей" if report_type == "morning" else "вечерний отчёт о выполненных работах"

        try:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"Пожалуйста, отправьте {report_name}:"
            )
            await query.answer("Проверьте личные сообщения для отправки отчёта.", show_alert=True)

        except TelegramError:
            del waiting_for_report[target_user_id]
            error_text = "Не удалось отправить вам личное сообщение. Пожалуйста, напишите боту в личные сообщения и попробуйте снова."
            try:
                await query.answer(error_text, show_alert=True)
            except BadRequest:
                await context.bot.send_message(
                    chat_id=group_id,
                    text=f"@{query.from_user.username}, {error_text}"
                )

    except BadRequest as e:
        if "Query is too old" in str(e):
            try:
                await context.bot.send_message(
                    chat_id=group_id,
                    text="⚠️ Это сообщение устарело. Пожалуйста, используйте актуальные кнопки для отправки отчета."
                )
            except TelegramError:
                pass

    except Exception as e:
        print(f"Unexpected error in button_handler: {e}")
        try:
            await query.answer("Произошла ошибка. Пожалуйста, попробуйте позже.", show_alert=True)
        except TelegramError:
            pass

# --- Обработчик ошибок ---

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

# --- Обработчик личных сообщений (отчётов) ---

async def handle_private_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id in waiting_for_report:
        report_info = waiting_for_report[user_id]
        report_type = report_info["report_type"]
        group_id = report_info["group_id"]

        if datetime.now(moscow_tz) - report_info["timestamp"] > timedelta(minutes=5):
            del waiting_for_report[user_id]
            await update.message.reply_text(
                "Время ожидания отчёта истекло. Пожалуйста, нажмите кнопку отправки отчёта в группе снова."
            )
            return

        today_str = datetime.now(moscow_tz).strftime("%Y-%m-%d")

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

        cursor.execute("""
        INSERT INTO reports (date, user_id, response, report_type, company, group_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (today_str, user_id, text, report_type, GROUPS[group_id][user_id]["company"], group_id))
        conn.commit()

        await update.message.reply_text("✅ Спасибо! Ваш отчёт принят.")

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

        del waiting_for_report[user_id]
    else:
        user_groups = [gid for gid, users in GROUPS.items() if user_id in users]
        if user_groups:
            await update.message.reply_text(
                "Для отправки отчёта используйте кнопку в групповом чате."
            )

# --- Обработчик сообщений в группах (для сохранения пользователей) ---

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

# --- Фоновые задачи после старта ---

async def post_init(application):
    asyncio.create_task(schedule_tasks(application))

# --- Команда выгрузки отчётов в Excel ---

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

    try:
        await context.bot.send_document(
            chat_id=user_id,
            document=InputFile(file_stream, filename=filename),
            caption=f"Отчёты: {report_type} за весь период"
        )
        await update.message.reply_text("Отчёт отправлен вам в личные сообщения.")
    except Exception:
        await update.message.reply_text(
            "Не удалось отправить файл в личные сообщения. "
            "Пожалуйста, начните чат с ботом и попробуйте снова."
        )

# --- Команда получения списка пользователей группы ---

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

# --- Команда помощи ---

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in ALLOWED_USERS:
        await update.message.reply_text("У вас нет прав на выполнение этой команды.")
        return

    help_text = (
        "Доступные команды:\n"
        "/menu — показать меню команд\n"
        "/daily_schedule — расписание сообщений\n"
        "/get_reports_xlsx <morning|evening> — выгрузить отчёты в Excel\n"
        "/get_group_users — получить список пользователей группы\n"
        "/help — показать это сообщение"
    )
    await update.message.reply_text(help_text)

# --- Команда /daily_schedule ---

async def daily_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in ALLOWED_USERS:
        await update.message.reply_text("У вас нет прав на выполнение этой команды.")
        return

    lines = []
    for group_id, users in GROUPS.items():
        lines.append(f"Группа ID {group_id}:")

        user_names = [user_data.get("name", f"User {uid}") for uid, user_data in users.items()]
        if user_names:
            lines.append("  Участники, которым будут отправлены сообщения:")
            for name in user_names:
                lines.append(f"    • {name}")
        else:
            lines.append("  Нет участников для отправки сообщений.")

        lines.append("  Расписание сообщений:")
        lines.append("    - 09:30 — Внимание! Срочно направьте информацию о количестве людей на площадке")
        # lines.append("    - 10:00 — Напоминание о утренних отчётах")  # если нужно раскомментировать
        lines.append("    - 19:00 — Напоминание о вечерних отчётах")
        lines.append("    - 21:00 — Сводка по вечерним отчётам\n")

    text = "Расписание отправки сообщений ботом в группах в течение дня:\n\n" + "\n".join(lines)

    await update.message.reply_text(text)

# --- Меню с кнопками ---

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in ALLOWED_USERS:
        await update.message.reply_text("У вас нет прав на выполнение этой команды.")
        return

    buttons = [
        [InlineKeyboardButton("📅 Расписание сообщений", callback_data="cmd_daily_schedule")],
        [InlineKeyboardButton("📊 Выгрузить отчёты (Excel)", callback_data="cmd_get_reports_xlsx")],
        [InlineKeyboardButton("👥 Список пользователей группы", callback_data="cmd_get_group_users")],
        [InlineKeyboardButton("❓ Помощь", callback_data="cmd_help")],
    ]

    reply_markup = InlineKeyboardMarkup(buttons)

    await update.message.reply_text(
        "Выберите команду:",
        reply_markup=reply_markup
    )

async def menu_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    if user_id not in ALLOWED_USERS:
        await query.answer("У вас нет прав на выполнение этой команды.", show_alert=True)
        return

    cmd = query.data

    if cmd == "cmd_daily_schedule":
        lines = []
        for group_id, users in GROUPS.items():
            lines.append(f"Группа ID {group_id}:")
            user_names = [user_data.get("name", f"User {uid}") for uid, user_data in users.items()]
            if user_names:
                lines.append("  Участники, которым будут отправлены сообщения:")
                for name in user_names:
                    lines.append(f"    • {name}")
            else:
                lines.append("  Нет участников для отправки сообщений.")

            lines.append("  Расписание сообщений:")
            lines.append("    - 09:30 — Внимание! Срочно направьте информацию о количестве людей на площадке")
            # lines.append("    - 10:00 — Напоминание о утренних отчётах")
            lines.append("    - 19:00 — Напоминание о вечерних отчётах")
            lines.append("    - 21:00 — Сводка по вечерним отчётам\n")

        text = "Расписание отправки сообщений ботом в группах в течение дня:\n\n" + "\n".join(lines)
        await query.message.edit_text(text)
    elif cmd == "cmd_get_reports_xlsx":
        await query.answer("Команду /get_reports_xlsx нужно вызывать из группового чата с параметрами.", show_alert=True)
    elif cmd == "cmd_get_group_users":
        await query.answer("Команду /get_group_users нужно вызывать из группового чата.", show_alert=True)
    elif cmd == "cmd_help":
        help_text = (
            "/menu — показать меню команд\n"
            "/daily_schedule — расписание сообщений (только для ALLOWED_USERS)\n"
            "Другие команды доступны в группах."
        )
        await query.message.edit_text(help_text)
    else:
        await query.answer("Неизвестная команда.", show_alert=True)

    await query.answer()

# --- Главная функция запуска ---

def main():
    try:
        app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()

        # Обработчики кнопок
        app.add_handler(CallbackQueryHandler(button_handler, pattern=r"^report_"))
        app.add_handler(CallbackQueryHandler(menu_button_handler, pattern=r"^cmd_"))

        # Личные сообщения
        app.add_handler(MessageHandler(
            filters.TEXT & filters.ChatType.PRIVATE & (~filters.COMMAND),
            handle_private_message
        ))

        # Сообщения в группах
        app.add_handler(MessageHandler(
            filters.TEXT & filters.ChatType.GROUPS & (~filters.COMMAND),
            handle_group_message
        ))

        # Команды
        app.add_handler(CommandHandler("get_reports_xlsx", get_reports_xlsx))
        app.add_handler(CommandHandler("get_group_users", get_group_users))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("daily_schedule", daily_schedule))
        app.add_handler(CommandHandler("menu", menu_command))

        # Обработчик ошибок
        app.add_error_handler(error_handler)

        print("Бот запущен и работает...")
        app.run_polling()

    except Exception as e:
        print(f"Critical error: {e}")

if __name__ == "__main__":
    main()
