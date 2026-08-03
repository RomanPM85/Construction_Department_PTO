import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("gemini_debug.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)

load_dotenv()

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    logging.error("Переменная GEMINI_API_KEY не найдена в .env")
    print("\n[ОШИБКА] Создайте файл .env и укажите в нем: GEMINI_API_KEY=AIzaSy...")
    sys.exit(1)

# Инициализация официального клиента Gemini
try:
    client = genai.Client(api_key=api_key)
except Exception as init_err:
    logging.error(f"Ошибка инициализации клиента: {init_err}")
    sys.exit(1)

# Выбор модели (gemini-2.5-flash оптимальна по скорости и стоимости)
MODEL_NAME = "gemini-2.5-flash"

# Настройка системной инструкции (System Prompt)
config = types.GenerateContentConfig(
    system_instruction="Ты полезный ИИ-ассистент. Отвечай кратко и по делу.",
)

# Инициализация сессии чата для автоматического управления контекстом
try:
    chat = client.chats.create(model=MODEL_NAME, config=config)
except Exception as chat_err:
    logging.error(f"Не удалось создать чат-сессию: {chat_err}")
    sys.exit(1)

# Буфер для порций текста и настройки сохранения
portion_buffer = []
PORTION_SIZE = 3
turn_counter = 0

print("\n=========================================================")
print(" Чат через официальный Gemini API запущен!")
print(f" Модель: {MODEL_NAME}")
print(f" Режим: Автосохранение в файл порциями каждые {PORTION_SIZE} диалога.")
print(" Для выхода из чата введите: exit или quit")
print("=========================================================\n")


def write_portion_to_disk(reason="по расписанию"):
    """Функция записи накопленного буфера на жесткий диск"""
    global portion_buffer
    if not portion_buffer:
        return

    history_file = "gemini_chat_history.txt"
    try:
        with open(history_file, "a", encoding="utf-8") as f:
            f.write(f"\n--- ЗАПИСЬ ПОРЦИИ ({reason}): {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
            f.writelines(portion_buffer)
            f.write("-----------------------------------------------------------------------\n")
        print(f"\n[СИСТЕМА] Порция из диалогов сохранена в {history_file}\n")
        portion_buffer.clear()
    except Exception as file_err:
        logging.error(f"Не удалось записать порцию на диск: {file_err}")
        print(f"\n[ОШИБКА СИСТЕМЫ] Не удалось записать порцию на диск: {file_err}\n")


while True:
    try:
        user_input = input("Вы: ")

        if user_input.strip().lower() in ['exit', 'quit']:
            if portion_buffer:
                write_portion_to_disk(reason="при выходе")
            print("До свидания!")
            break

        if not user_input.strip():
            continue

        # Логируем отправку и добавляем реплику пользователя в буфер файла
        portion_buffer.append(f"[{datetime.now().strftime('%H:%M:%S')}] Вы: {user_input}\n")
        logging.info("Отправка запроса в Gemini API...")

        print("\nGemini: ", end="", flush=True)

        full_ai_response = ""

        # Стриминг ответа через официальный метод
        response_stream = chat.send_message_stream(user_input)

        for chunk in response_stream:
            if chunk.text:
                print(chunk.text, end="", flush=True)
                full_ai_response += chunk.text

        print("\n")
        logging.info("Ответ от Gemini успешно получен.")

        # Добавляем ответ ИИ в буфер файла (в контексте чата он сохраняется сам)
        portion_buffer.append(f"[{datetime.now().strftime('%H:%M:%S')}] Gemini: {full_ai_response}\n")

        # Проверка лимита порции
        turn_counter += 1
        if turn_counter >= PORTION_SIZE:
            write_portion_to_disk(reason="лимит порции достигнут")
            turn_counter = 0

    except KeyboardInterrupt:
        if portion_buffer:
            write_portion_to_disk(reason="аварийное завершение Ctrl+C")
        print("\n\nПрограмма принудительно завершена.")
        break
    except Exception as e:
        logging.exception(f"Непредвиденная ошибка: {e}")
        print(f"\n[КРИТИЧЕСКАЯ ОШИБКА] Сбой: {e}. Подробности в gemini_debug.log\n")
