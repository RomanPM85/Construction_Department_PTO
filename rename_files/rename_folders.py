import pathlib
import logging

# Настройка логирования
logging.basicConfig(filename='log.txt', level=logging.INFO, format='%(message)s')

def rename_folders(base_path):
    # Перебор всех папок в указанном пути рекурсивно
    for path in base_path.rglob('*'):
        if path.is_dir() and path.name.startswith("Исходные_файлы_ИД"):
            new_name = path.parent / "Draft_version"
            try:
                # Переименование папки
                path.rename(new_name)
                logging.info(f"Переименовано: {path} -> {new_name}")
            except Exception as e:
                logging.error(f"Ошибка при переименовании {path}: {e}")

if __name__ == "__main__":
    current_path = pathlib.Path.cwd()  # Получаем текущую директорию
    rename_folders(current_path)
