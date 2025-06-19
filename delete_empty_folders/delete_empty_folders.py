from pathlib import Path


def remove_empty_folders(directory='.'):
    directory = Path(directory)

    # Используем .rglob для рекурсивного поиска от текущей директории
    for item in directory.rglob('*'):
        if item.is_dir():
            # Проверяем, что в директории нет файлов и поддиректорий
            if not any(item.iterdir()):
                try:
                    item.rmdir()
                    print(f"Удалена пустая папка: {item}")
                except Exception as e:
                    print(f"Ошибка при удалении {item}: {e}")


# Использование от текущей директории
if __name__ == '__main__':
    remove_empty_folders()
