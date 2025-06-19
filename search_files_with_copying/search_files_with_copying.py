from pathlib import Path
import shutil
import re


def search_and_copy_files(
        source_directory,
        destination_directory,
        search_text,
        file_types=None,
        recursive=True
):
    """
    Поиск и копирование файлов по части текста.

    Параметры:
    - source_directory: путь к исходной директории для поиска
    - destination_directory: путь к директории для копирования найденных файлов
    - search_text: текст для поиска в файлах
    - file_types: список расширений файлов для поиска (необязательно)
    - recursive: поиск во вложенных директориях (по умолчанию True)
    """
    # Преобразуем пути в объекты Path
    source_path = Path(source_directory).resolve()
    dest_path = Path(destination_directory).resolve()

    # Создаем директорию назначения, если она не существует
    dest_path.mkdir(parents=True, exist_ok=True)

    # Счетчики
    total_files_checked = 0
    files_found = 0

    # Определяем шаблон поиска файлов
    if file_types:
        # Если указаны конкретные типы файлов
        file_pattern = [f'*.{ext}' for ext in file_types]
    else:
        # Поиск по всем файлам
        file_pattern = ['*']

    # Функция поиска текста в файле
    def search_in_file(file_path):
        try:
            # Открываем файл с возможными кодировками
            encoding_list = ['utf-8', 'cp1251', 'latin1', 'utf-16']
            for encoding in encoding_list:
                try:
                    with file_path.open('r', encoding=encoding) as f:
                        content = f.read()
                        # Поиск с учетом регистра
                        if search_text.lower() in content.lower():
                            return True
                    break
                except UnicodeDecodeError:
                    continue
        except Exception as e:
            print(f"Ошибка чтения файла {file_path}: {e}")
        return False

    # Рекурсивный поиск файлов
    search_method = source_path.rglob if recursive else source_path.glob

    # Поиск и копирование файлов
    for pattern in file_pattern:
        for file_path in search_method(pattern):
            # Пропускаем директории
            if file_path.is_dir():
                continue

            total_files_checked += 1

            # Проверка содержимого файла
            if search_in_file(file_path):
                files_found += 1

                # Формируем путь для копирования с сохранением структуры
                relative_path = file_path.relative_to(source_path)
                new_file_path = dest_path / relative_path

                # Создаем промежуточные директории
                new_file_path.parent.mkdir(parents=True, exist_ok=True)

                # Копирование файла
                try:
                    shutil.copy2(file_path, new_file_path)
                    print(f"Скопирован файл: {file_path}")
                except Exception as e:
                    print(f"Ошибка копирования {file_path}: {e}")

    # Вывод статистики
    print("\n--- Статистика ---")
    print(f"Всего проверено файлов: {total_files_checked}")
    print(f"Найдено и скопировано файлов: {files_found}")


# Пример использования
if __name__ == "__main__":
    search_and_copy_files(
        source_directory=r"C:\Users\Username\Documents",  # Путь к исходной директории
        destination_directory=r"C:\Temp\Found_Files",  # Путь к директории для копирования
        search_text="важный текст",  # Текст для поиска
        file_types=['txt', 'docx', 'pdf'],  # Типы файлов (необязательно)
        recursive=True  # Поиск во вложенных директориях
    )
