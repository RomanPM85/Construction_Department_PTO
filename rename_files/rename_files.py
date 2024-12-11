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


# Пример использования:
# folder_path = os.getcwd()  # Текущая папка

directory_to_rename = Path.cwd()  # Замените на путь к вашей папке
rename_files(directory_to_rename)
