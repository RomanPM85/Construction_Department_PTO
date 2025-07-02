from pathlib import Path
import shutil
from datetime import datetime

# Получаем текущую директорию
current_dir = Path.cwd()

# Проходим по всем файлам в текущей директории
for file in current_dir.iterdir():
    if file.is_file():  # Проверяем, является ли элемент файлом
        # Получаем дату изменения файла
        modified_time = file.stat().st_mtime
        modified_date = datetime.fromtimestamp(modified_time).date()

        # Создаем имя папки по дате изменения
        folder_name = modified_date.strftime("%Y-%m-%d")  # Формат YYYY-MM-DD
        folder_path = current_dir / folder_name

        # Создаем папку, если она не существует
        folder_path.mkdir(exist_ok=True)

        # Перемещаем файл в соответствующую папку
        shutil.move(str(file), str(folder_path / file.name))

print("Файлы успешно сгруппированы по дате изменения.")
