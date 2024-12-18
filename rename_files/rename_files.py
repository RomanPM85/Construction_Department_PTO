import os
import re
from pathlib import Path


def rename_files(directory):
    """Переименовывает файлы в формате 'текст№1_текст' в 'текст№001_текст'."""
    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    files.sort()  # Сортируем файлы для корректной нумерации

    for i, filename in enumerate(files):
        match = re.match(r"(.*)№(\d+)(.*)", filename)  # Регулярное выражение для поиска шаблона
        if match:
            prefix = match.group(1)
            number = int(match.group(2))
            suffix = match.group(3)
            new_filename = f"{prefix}№{number:03d}_{suffix}"  # Форматирование номера с ведущими нулями
            old_filepath = os.path.join(directory, filename)
            new_filepath = os.path.join(directory, new_filename)
            os.rename(old_filepath, new_filepath)
            print(f"Переименовано: {filename} -> {new_filename}")


def safe_rename_files(directory, pattern, replacement=""):
    """Переименовывает файлы, обрабатывая потенциальные ошибки."""
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath):  # Проверка, является ли это файлом
            new_filename = re.sub(pattern, replacement, filename)
            if filename != new_filename:
                new_filepath = os.path.join(directory, new_filename)
            try:
                os.rename(filepath, new_filepath)
                print(f"Файл '{filename}' переименован в '{new_filename}'")
            except OSError as e:
                print(f"Ошибка переименования файла '{filename}': {e}")

# Пример использования:
# folder_path = os.getcwd()  # Текущая папка


if __name__ == "__main__":
    directory_to_rename = Path.cwd()  # Замените на путь к вашей папке
    # rename_files(directory_to_rename)
    safe_rename_files(directory_to_rename, r"[ \t\r\n]+")