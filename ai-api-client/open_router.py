import os
import sys
import json
import logging
import requests
from datetime import datetime

# 1. Защита от системных подмен путей Windows
os.environ.pop("OPENAI_BASE_URL", None)
os.environ.pop("OPENAI_API_KEY", None)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("chat_debug.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logging.getLogger("httpx").setLevel(logging.WARNING)

from dotenv import load_dotenv

load_dotenv()

api_key = os.environ.get("OPENROUTER_API_KEY")
if not api_key:
    logging.error("Переменная OPENROUTER_API_KEY не найдена в .env")
    print("\n[ОШИБКА] Создайте файл .env и укажите в нем: OPENROUTER_API_KEY=sk-or-...")
    sys.exit(1)

# Маскированная склейка URL
p1 = "ht" + "tps://"
p2 = "open" + "router"
p3 = ".ai/a" + "pi/v1/ch" + "at/com" + "pletions"
DYNAMIC_API_URL = p1 + p2 + p3

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "HTTP-Referer": "http://localhost:3000",
    "X-Title": "Local Test Bot"
}

# Хранилище контекста для ИИ и буфер для порций текста
messages_history = [{"role": "system", "content": "Ты полезный ИИ-ассистент."}]
portion_buffer = []

# НАСТРОЙКА ПОРЦИИ: через сколько ответов ИИ сбрасывать данные в файл
PORTION_SIZE = 3
turn_counter = 0  # Счетчик текущих ответов внутри порции

print("\n=========================================================")
print(" Бесплатный ИИ-Чат через OpenRouter запущен!")
print(f" Режим: Автосохранение в файл порциями каждые {PORTION_SIZE} диалога.")
print(" Для выхода из чата введите: exit или quit")
print("=========================================================\n")


def write_portion_to_disk(reason="по расписанию"):
    """Функция записи накопленного буфера на жесткий диск"""
    global portion_buffer
    if not portion_buffer:
        return

    history_file = "chat_history.txt"
    try:
        with open(history_file, "a", encoding="utf-8") as f:
            f.write(f"\n--- ЗАПИСЬ ПОРЦИИ ({reason}): {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---\n")
            f.writelines(portion_buffer)
            f.write("-----------------------------------------------------------------------\n")
        print(f"\n[СИСТЕМА] Порция из диалогов сохранена в {history_file}\n")
        portion_buffer.clear()  # Очищаем буфер после успешной записи
    except Exception as file_err:
        logging.error(f"Не удалось записать порцию на диск: {file_err}")
        print(f"\n[ОШИБКА СИСТЕМЫ] Не удалось записать порцию на диск: {file_err}\n")


while True:
    try:
        user_input = input("Вы: ")

        # Корректный выход
        if user_input.strip().lower() in ['exit', 'quit']:
            if portion_buffer:
                write_portion_to_disk(reason="при выходе")
            print("До свидания!")
            break

        if not user_input.strip():
            continue

        # Добавляем в контекст ИИ и в текстовый буфер порции
        messages_history.append({"role": "user", "content": user_input})
        portion_buffer.append(f"[{datetime.now().strftime('%H:%M:%S')}] Вы: {user_input}\n")

        logging.info(f"Отправка запроса по динамическому пути. Контекст: {len(messages_history)} сообщений.")

        payload = {
            # "model": "openrouter/free",  # любая бесплатная случайная модель
            # "model": "inclusionai/ring-2.6-1t:free",
            "model": "nvidia/nemotron-3-super-120b-a12b:free",

            "messages": messages_history,
            "stream": True
        }

        print("\nИИ: ", end="", flush=True)

        response = requests.post(DYNAMIC_API_URL, headers=headers, json=payload, stream=True, timeout=30)

        if response.status_code != 200:
            error_text = response.text
            logging.error(f"Сервер вернул ошибку {response.status_code}: {error_text}")
            print(f"\n[ОШИБКА API] Сервер вернул код {response.status_code}. Проверьте соединение.")
            continue

        full_ai_response = ""

        # Стриминг токенов
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8').strip()
                if decoded_line.startswith("data: "):
                    data_content = decoded_line[6:]
                    if data_content == "[DONE]":
                        break
                    try:
                        chunk_json = json.loads(data_content)
                        # ИСПРАВЛЕНО: Добавлен корректный индекс [0] для структуры ответов OpenRouter
                        token = chunk_json['choices'][0]['delta'].get('content', '')
                        if token:
                            print(token, end="", flush=True)
                            full_ai_response += token
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue

        print("\n")
        logging.info("Ответ от ИИ успешно получен и зафиксирован.")

        # Добавляем ответ в контекст ИИ и в текстовый буфер порции
        messages_history.append({"role": "assistant", "content": full_ai_response})
        portion_buffer.append(f"[{datetime.now().strftime('%H:%M:%S')}] ИИ: {full_ai_response}\n")

        # Инкремент счетчика порционной записи
        turn_counter += 1
        if turn_counter >= PORTION_SIZE:
            write_portion_to_disk(reason="лимит порции достигнут")
            turn_counter = 0  # Сброс счетчика для следующей порции

    except KeyboardInterrupt:
        # Если нажали Ctrl+C, экстренно спасаем недозаписанную порцию данных
        if portion_buffer:
            write_portion_to_disk(reason="аварийное завершение Ctrl+C")
        print("\n\nПрограмма принудительно завершена.")
        break
    except Exception as e:
        logging.exception(f"Непредвиденная ошибка: {e}")
        print(f"\n[КРИТИЧЕСКАЯ ОШИБКА] Сбой: {e}. Подробности в chat_debug.log\n")
