import os
from dotenv import load_dotenv
from openai import OpenAI

# Загрузка переменных из файла .env
load_dotenv()

# Проверка, что ключ успешно загружен
if not os.environ.get("DEEPSEEK_API_KEY"):
    raise ValueError("Ошибка: DEEPSEEK_API_KEY не найден в файле .env")

# Инициализация клиента DeepSeek
client = OpenAI(
    base_url="https://api.deepseek.com",  # Обязательно с https:// и поддоменом api
    api_key=os.environ.get("DEEPSEEK_API_KEY")
)

messages_history = [
    {"role": "system", "content": "Ты — глубоко мыслящий ИИ-ассистент."}
]

print("Чат запущен через .env! Для выхода напишите 'exit'.\n")

while True:
    try:
        user_input = input("Вы: ")
        if user_input.lower() in ['exit', 'quit']:
            print("До свидания!")
            break

        if not user_input.strip():
            continue

        messages_history.append({"role": "user", "content": user_input})

        response = client.chat.completions.create(
            model="deepseek-reasoner",
            messages=messages_history,
            stream=False
        )

        ai_response = response.choices.message.content
        print(f"\nAI: {ai_response}\n")

        messages_history.append({"role": "assistant", "content": ai_response})

    except Exception as e:
        print(f"\nПроизошла ошибка: {e}\n")
