import json
import os


def txt_to_amnezia_json():
    # Запрос имени файла у пользователя
    input_txt = input("Введите имя или путь к исходному TXT-файлу: ").strip()

    # Автоматическое добавление расширения .txt, если пользователь его не указал
    if not input_txt.lower().endswith('.txt') and not os.path.exists(input_txt):
        input_txt += '.txt'

    # Проверка существования файла
    if not os.path.exists(input_txt):
        print(f"Ошибка: Файл '{input_txt}' не найден.")
        return

    # Получаем чистое имя файла без пути и без расширения .txt
    base_name = os.path.splitext(os.path.basename(input_txt))[0]
    # Формируем имя выходного файла по маске amnezia_(указанный_файл).json
    output_json = f"amnezia_{base_name}.json"

    amnezia_list = []

    try:
        with open(input_txt, 'r', encoding='utf-8') as txt_file:
            for line in txt_file:
                line = line.strip()

                # Игнорируем пустые строки и комментарии
                if not line or line.startswith('#'):
                    continue

                # Структура для AmneziaVPN Split Tunneling
                amnezia_list.append({
                    "hostname": line,
                    "ip": ""
                })

        with open(output_json, 'w', encoding='utf-8') as json_file:
            json.dump(amnezia_list, json_file, ensure_ascii=False, indent=2)

        print(f"\nУспешно! Создан файл: '{output_json}'")
        print(f"Количество добавленных записей: {len(amnezia_list)}")

    except Exception as e:
        print(f"Произошла ошибка при обработке файла: {e}")


if __name__ == "__main__":
    txt_to_amnezia_json()
