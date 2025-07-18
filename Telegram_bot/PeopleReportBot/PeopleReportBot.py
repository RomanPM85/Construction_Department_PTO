import asyncio
from datetime import datetime, time
import pytz
import sqlite3
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

from config import TOKEN, GROUPS

moscow_tz = pytz.timezone("Europe/Moscow")

conn = sqlite3.connect("reports.db", check_same_thread=False)
cursor = conn.cursor()

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
conn.commit()

async def send_report_request_in_group(app, group_id, user_id, report_type):
    user_data = GROUPS[group_id][user_id]
    user_name = user_data["name"]
    if report_type == "morning":
        text = f"Доброе утро, [{user_name}](tg://user?id={user_id})! Пожалуйста, пришлите отчёт о количестве людей на объекте."
    else:
        text = f"Добрый вечер, [{user_name}](tg://user?id={user_id})! Пожалуйста, пришлите краткий отчёт о выполненных работах."

    try:
        await app.bot.send_message(chat_id=group_id, text=text, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        print(f"Ошибка при отправке сообщения в группу {group_id}: {e}")

async def remind_unanswered(app, group_id, report_type):
    today = datetime.now(moscow_tz).strftime("%Y-%m-%d")
    for user_id in GROUPS[group_id]:
        cursor.execute("""
        SELECT COUNT(*) FROM reports 
        WHERE date=? AND user_id=? AND report_type=? AND group_id=?
        """, (today, user_id, report_type, group_id))
        count = cursor.fetchone()[0]
        if count == 0:
            try:
                user_name = GROUPS[group_id][user_id]["name"]
                text = f"Напоминание, [{user_name}](tg://user?id={user_id}): пожалуйста, пришлите { 'утренний' if report_type == 'morning' else 'вечерний' } отчёт."
                await app.bot.send_message(chat_id=group_id, text=text, parse_mode=ParseMode.MARKDOWN)
            except Exception as e:
                print(f"Ошибка напоминания в группе {group_id}: {e}")

async def schedule_tasks(app):
    while True:
        now = datetime.now(moscow_tz)
        today_str = now.strftime("%Y-%m-%d")

        morning_time = time(9, 0, 0)
        evening_time = time(18, 0, 0)

        for group_id, users in GROUPS.items():
            # Утренние запросы
            if now.time() >= morning_time:
                cursor.execute("""
                SELECT COUNT(*) FROM reports WHERE date=? AND report_type='morning' AND group_id=?
                """, (today_str, group_id))
                total_morning = cursor.fetchone()[0]
                if total_morning < len(users):
                    for user_id in users:
                        cursor.execute("""
                        SELECT COUNT(*) FROM reports WHERE date=? AND user_id=? AND report_type='morning' AND group_id=?
                        """, (today_str, user_id, group_id))
                        if cursor.fetchone()[0] == 0:
                            await send_report_request_in_group(app, group_id, user_id, "morning")

            # Вечерние запросы
            if now.time() >= evening_time:
                cursor.execute("""
                SELECT COUNT(*) FROM reports WHERE date=? AND report_type='evening' AND group_id=?
                """, (today_str, group_id))
                total_evening = cursor.fetchone()[0]
                if total_evening < len(users):
                    for user_id in users:
                        cursor.execute("""
                        SELECT COUNT(*) FROM reports WHERE date=? AND user_id=? AND report_type='evening' AND group_id=?
                        """, (today_str, user_id, group_id))
                        if cursor.fetchone()[0] == 0:
                            await send_report_request_in_group(app, group_id, user_id, "evening")

            # Напоминания по утреннему отчету (с 10:00 до 17:00)
            if time(10, 0, 0) <= now.time() < evening_time:
                await remind_unanswered(app, group_id, "morning")

            # Напоминания по вечернему отчету (с 19:00 до 23:00)
            if time(19, 0, 0) <= now.time() <= time(23, 0, 0):
                await remind_unanswered(app, group_id, "evening")

        await asyncio.sleep(60)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    user_groups = [gid for gid, users in GROUPS.items() if user_id in users]
    if not user_groups:
        return  # Игнорируем сообщения от незарегистрированных пользователей

    today_str = datetime.now(moscow_tz).strftime("%Y-%m-%d")
    text = update.message.text

    now = datetime.now(moscow_tz).time()
    morning_time = time(9, 0, 0)
    evening_time = time(18, 0, 0)
    report_type = "morning" if morning_time <= now < evening_time else "evening"

    for group_id in user_groups:
        cursor.execute("""
        SELECT COUNT(*) FROM reports WHERE date=? AND user_id=? AND report_type=? AND group_id=?
        """, (today_str, user_id, report_type, group_id))
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
            INSERT INTO reports (date, user_id, response, report_type, company, group_id) VALUES (?, ?, ?, ?, ?, ?)
            """, (today_str, user_id, text, report_type, GROUPS[group_id][user_id]["company"], group_id))
            conn.commit()
            await update.message.reply_text("Спасибо за отчёт!")
        else:
            await update.message.reply_text("Отчёт на сегодня уже получен.")

async def post_init(application):
    """Запускаем фоновые задачи после инициализации приложения"""
    asyncio.create_task(schedule_tasks(application))

def main():
    app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()

    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("Бот запущен и работает...")
    app.run_polling()

if __name__ == "__main__":
    main()
