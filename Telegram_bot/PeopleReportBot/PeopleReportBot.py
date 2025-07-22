import asyncio
from datetime import datetime, time, timedelta
import pytz
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CallbackQueryHandler, \
    ConversationHandler, CommandHandler

from config import TOKEN, GROUPS

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
conn.commit()

# Состояние для ConversationHandler — ожидание отчета
WAITING_FOR_REPORT = 1

# Словарь для хранения контекста ожидания отчета от пользователей
waiting_for_report = {}


async def send_report_request_in_group(app, group_id, user_id, report_type, is_reminder=False):
    user_data = GROUPS[group_id][user_id]
    user_name = user_data["name"]

    if is_reminder:
        if report_type == "morning":
            text = f"Напоминание, [{user_name}](tg://user?id={user_id}): пожалуйста, пришлите утренний отчёт о количестве людей на объекте."
        else:
            text = f"Напоминание, [{user_name}](tg://user?id={user_id}): пожалуйста, пришлите вечерний отчёт о выполненных работах."
    else:
        if report_type == "morning":
            text = f"Доброе утро, [{user_name}](tg://user?id={user_id})! Пожалуйста, пришлите отчёт о количестве людей на объекте."
        else:
            text = f"Добрый вечер, [{user_name}](tg://user?id={user_id})! Пожалуйста, пришлите краткий отчёт о выполненных работах."

    # Создаем клавиатуру с кнопкой для отправки отчёта
    keyboard = [[InlineKeyboardButton("📝 Отправить отчёт", callback_data=f"report_{report_type}_{user_id}_{group_id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await app.bot.send_message(
            chat_id=group_id,
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )

        # Записываем факт отправки сообщения в базу
        now = datetime.now(moscow_tz)
        message_type = f"{report_type}_{'reminder' if is_reminder else 'initial'}"
        cursor.execute("""
        INSERT INTO sent_messages (date, user_id, group_id, message_type, sent_at) 
        VALUES (?, ?, ?, ?, ?)
        """, (now.strftime("%Y-%m-%d"), user_id, group_id, message_type, now))
        conn.commit()

    except Exception as e:
        print(f"Ошибка при отправке сообщения в группу {group_id}: {e}")


async def send_pending_reports_notification(app, group_id, report_type):
    today_str = datetime.now(moscow_tz).strftime("%Y-%m-%d")
    users = GROUPS[group_id]

    pending_users = []

    for user_id, user_data in users.items():
        cursor.execute("""
        SELECT COUNT(*) FROM reports 
        WHERE date=? AND user_id=? AND report_type=? AND group_id=?
        """, (today_str, user_id, report_type, group_id))
        sent = cursor.fetchone()[0] > 0
        if not sent:
            pending_users.append(user_data["name"])

    if not pending_users:
        if report_type == "morning":
            text = "☀️ Все утренние отчёты получены."
        else:
            text = "🌙 Все вечерние отчёты получены."
    else:
        if report_type == "morning":
            text = "☀️ *Ожидаются утренние отчёты от:*\n" + "\n".join(f"• {name}" for name in pending_users)
        else:
            text = "🌙 *Ожидаются вечерние отчёты от:*\n" + "\n".join(f"• {name}" for name in pending_users)

    await app.bot.send_message(
        chat_id=group_id,
        text=text,
        parse_mode=ParseMode.MARKDOWN
    )


async def check_last_message_time(user_id, group_id, message_type, date):
    """Проверяет, прошло ли 60 минут с последнего сообщения данного типа"""
    cursor.execute("""
    SELECT sent_at FROM sent_messages 
    WHERE date=? AND user_id=? AND group_id=? AND message_type LIKE ?
    ORDER BY sent_at DESC LIMIT 1
    """, (date, user_id, group_id, f"%{message_type}%"))

    result = cursor.fetchone()
    if result:
        last_sent = datetime.fromisoformat(result[0])
        if isinstance(last_sent, str):
            last_sent = datetime.strptime(last_sent, "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=moscow_tz)
        now = datetime.now(moscow_tz)
        # Возвращаем True, если прошло не менее 60 минут
        return (now - last_sent) >= timedelta(minutes=60)
    return True


async def schedule_tasks(app):
    # Флаги для отслеживания отправленных первых сообщений
    morning_initial_sent = {}
    evening_initial_sent = {}

    morning_summary_sent = set()  # Чтобы отправить раз в день
    evening_summary_sent = set()

    while True:
        now = datetime.now(moscow_tz)
        today_str = now.strftime("%Y-%m-%d")
        current_time = now.time()

        morning_time = time(10, 0, 0)
        evening_time = time(19, 0, 0)

        for group_id, users in GROUPS.items():
            if group_id not in morning_initial_sent:
                morning_initial_sent[group_id] = {}
            if group_id not in evening_initial_sent:
                evening_initial_sent[group_id] = {}

            for user_id in users:
                # Проверяем, отправлен ли утренний отчет сегодня
                cursor.execute("""
                SELECT COUNT(*) FROM reports 
                WHERE date=? AND user_id=? AND report_type='morning' AND group_id=?
                """, (today_str, user_id, group_id))
                morning_sent = cursor.fetchone()[0] > 0

                # Проверяем, отправлен ли вечерний отчет сегодня
                cursor.execute("""
                SELECT COUNT(*) FROM reports 
                WHERE date=? AND user_id=? AND report_type='evening' AND group_id=?
                """, (today_str, user_id, group_id))
                evening_sent = cursor.fetchone()[0] > 0

                # Утренние сообщения (с 10:00 до 19:00)
                if morning_time <= current_time < evening_time and not morning_sent:
                    if user_id not in morning_initial_sent[group_id]:
                        cursor.execute("""
                        SELECT COUNT(*) FROM sent_messages 
                        WHERE date=? AND user_id=? AND group_id=? AND message_type='morning_initial'
                        """, (today_str, user_id, group_id))
                        morning_initial_sent[group_id][user_id] = cursor.fetchone()[0] > 0

                    if not morning_initial_sent[group_id][user_id]:
                        await send_report_request_in_group(app, group_id, user_id, "morning", is_reminder=False)
                        morning_initial_sent[group_id][user_id] = True

                # Вечерние сообщения (с 19:00 и далее)
                if current_time >= evening_time and not evening_sent:
                    if user_id not in evening_initial_sent[group_id]:
                        cursor.execute("""
                        SELECT COUNT(*) FROM sent_messages 
                        WHERE date=? AND user_id=? AND group_id=? AND message_type='evening_initial'
                        """, (today_str, user_id, group_id))
                        evening_initial_sent[group_id][user_id] = cursor.fetchone()[0] > 0

                    if not evening_initial_sent[group_id][user_id]:
                        await send_report_request_in_group(app, group_id, user_id, "evening", is_reminder=False)
                        evening_initial_sent[group_id][user_id] = True

            # Отправляем сводное сообщение утром после 10:05 (один раз в день)
            if current_time >= time(10, 5, 0) and group_id not in morning_summary_sent:
                await send_pending_reports_notification(app, group_id, "morning")
                morning_summary_sent.add(group_id)

            # Отправляем сводное сообщение вечером после 19:05 (один раз в день)
            if current_time >= time(19, 5, 0) and group_id not in evening_summary_sent:
                await send_pending_reports_notification(app, group_id, "evening")
                evening_summary_sent.add(group_id)

        # Сброс флагов в полночь
        if current_time < time(0, 1, 0):
            morning_initial_sent.clear()
            evening_initial_sent.clear()
            morning_summary_sent.clear()
            evening_summary_sent.clear()

        await asyncio.sleep(30)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("report_"):
        parts = query.data.split("_")
        report_type = parts[1]
        target_user_id = int(parts[2])
        group_id = int(parts[3])

        # Проверяем, что кнопку нажал именно тот пользователь, для которого она предназначена
        if query.from_user.id != target_user_id:
            await query.answer("Эта кнопка предназначена для другого пользователя!", show_alert=True)
            return

        # Сохраняем контекст ожидания отчёта
        waiting_for_report[target_user_id] = {
            "report_type": report_type,
            "group_id": group_id,
            "message_id": query.message.message_id
        }

        # Отправляем личное сообщение пользователю с просьбой отправить отчёт
        report_name = "утренний отчёт о количестве людей" if report_type == "morning" else "вечерний отчёт о выполненных работах"
        await context.bot.send_message(
            chat_id=target_user_id,
            text=f"Пожалуйста, отправьте {report_name}:"
        )

        await query.edit_message_text(
            text=query.message.text + "\n\n_Ожидается отчёт в личных сообщениях..._",
            parse_mode=ParseMode.MARKDOWN
        )


async def handle_private_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    # Проверяем, ожидаем ли отчёт от этого пользователя
    if user_id in waiting_for_report:
        report_info = waiting_for_report[user_id]
        report_type = report_info["report_type"]
        group_id = report_info["group_id"]

        today_str = datetime.now(moscow_tz).strftime("%Y-%m-%d")
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
    # В группе обрабатываем только команды, остальное игнорируем
    pass


async def post_init(application):
    """Запускаем фоновые задачи после инициализации приложения"""
    asyncio.create_task(schedule_tasks(application))


def main():
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()

    # Обработчик нажатий кнопок
    app.add_handler(CallbackQueryHandler(button_handler))

    # Обработчик личных сообщений
    app.add_handler(MessageHandler(
        filters.TEXT & filters.ChatType.PRIVATE & (~filters.COMMAND),
        handle_private_message
    ))

    # Обработчик сообщений в группах (если нужно)
    app.add_handler(MessageHandler(
        filters.TEXT & filters.ChatType.GROUPS & (~filters.COMMAND),
        handle_group_message
    ))

    print("Бот запущен и работает...")
    app.run_polling()


if __name__ == "__main__":
    main()
