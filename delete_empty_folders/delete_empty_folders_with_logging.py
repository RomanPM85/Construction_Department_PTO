from pathlib import Path
import logging
from datetime import datetime


def remove_empty_folders(directory='.', log_file='log.txt'):
    # Настройка логирования
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Преобразование пути директории
    directory = Path(directory).resolve()

    # Счетчики
    total_checked = 0
    total_removed = 0

    try:
        # Список для хранения путей всех пустых папок
        empty_folders = []

        # Рекурсивный поиск пустых папок
        for item in sorted(directory.rglob('*'), key=lambda x: len(str(x)), reverse=True):
            if item.is_dir():
                total_checked += 1

                # Проверка на пустоту директории
                try:
                    if not any(item.iterdir()):
                        empty_folders.append(item)
                except PermissionError:
                    logging.warning(f"Нет доступа к директории: {item}")

        # Удаление пустых папок
        for folder in empty_folders:
            try:
                folder.rmdir()
                logging.info(f"Удалена пустая папка: {folder}")
                total_removed += 1
            except Exception as e:
                logging.error(f"Ошибка при удалении {folder}: {e}")

        # Итоговая статистика
        logging.info(f"Всего проверено директорий: {total_checked}")
        logging.info(f"Удалено пустых директорий: {total_removed}")

        print(f"Проверка завершена. Удалено пустых папок: {total_removed}")

    except Exception as e:
        logging.error(f"Критическая ошибка: {e}")
        print(f"Произошла ошибка: {e}")


def main():
    # Получаем текущую директорию
    current_dir = Path.cwd()

    # Формирование имени лог-файла с меткой времени
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"empty_folders_removal_{timestamp}.txt"

    # Вызов функции удаления
    remove_empty_folders(current_dir, log_filename)


if __name__ == '__main__':
    main()
