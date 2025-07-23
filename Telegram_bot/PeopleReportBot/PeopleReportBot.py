import asyncio
from datetime import datetime, time, timedelta
import pytz
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CallbackQueryHandler, \
    ConversationHandler, CommandHandler
from telegram.error import BadRequest, TelegramError
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


async def send_report_request_with_buttons(app, group_id, report_type):
    today_str = datetime.now(moscow_tz).strftime("%Y-%m-%d")
    users = GROUPS[group_id]

    # Список пользователей, которые должны отправить отчёт
    pending_users = []
    for user_id, user_data in users.items():
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

    # Формируем текст и кнопки
    buttons = []
    text_lines = [header]
    for user_id, name in pending_users:  # Изменено: user_data -> name
        text_lines.append(f"• {name}")  # Изменено: user_data['name'] -> name
        buttons.append([InlineKeyboardButton(f"📝 Отправить отчёт ({name})",  # Изменено: user_data['name'] -> name
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

    morning_sent = []
    morning_pending = []
    evening_sent = []
    evening_pending = []

    for user_id, user_data in users.items():
        cursor.execute("""
        SELECT COUNT(*) FROM reports
        WHERE date=? AND user_id=? AND report_type='morning' AND group_id=?
        """, (today_str, user_id, group_id))
        if cursor.fetchone()[0] > 0:
            morning_sent.append(user_data["name"])
        else:
            morning_pending.append(user_data["name"])

        cursor.execute("""
        SELECT COUNT(*) FROM reports
        WHERE date=? AND user_id=? AND report_type='evening' AND group_id=?
        """, (today_str, user_id, group_id))
        if cursor.fetchone()[0] > 0:
            evening_sent.append(user_data["name"])
        else:
            evening_pending.append(user_data["name"])

    text = "🕘 *Сводка по отчётам за сегодня:*\n\n"

    text += "☀️ *Утренний отчёт:*\n"
    text += "✅ Отправили:\n" + ("\n".join(f"• {n}" for n in morning_sent) if morning_sent else "• Никто") + "\n"
    text += "⚠️ Не отправили:\n" + ("\n".join(f"• {n}" for n in morning_pending) if morning_pending else "• Все") + "\n\n"

    text += "🌙 *Вечерний отчёт:*\n"
    text += "✅ Отправили:\n" + ("\n".join(f"• {n}" for n in evening_sent) if evening_sent else "• Никто") + "\n"
    text += "⚠️ Не отправили:\n" + ("\n".join(f"• {n}" for n in evening_pending) if evening_pending else "• Все") + "\n"

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
        group_ids = GROUPS.keys()

        for group_id in group_ids:
            if current_time >= time(10, 0) and group_id not in sent_10:
                await send_report_request_with_buttons(app, group_id, "morning")
                sent_10.add(group_id)

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
    # В группе обрабатываем только команды, остальное игнорируем
    pass


async def post_init(application):
    """Запускаем фоновые задачи после инициализации приложения"""
    asyncio.create_task(schedule_tasks(application))


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

        # Добавляем обработчик ошибок
        app.add_error_handler(error_handler)

        print("Бот запущен и работает...")
        app.run_polling()

    except Exception as e:
        print(f"Critical error: {e}")
        # Можно добавить логирование или отправку уведомления администратору


if __name__ == "__main__":
    main()
