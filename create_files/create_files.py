from pathlib import Path
import shutil

# Определяем путь к текущей директории
current_folder = Path.cwd()
template_file = current_folder / 'Спецификация_template.xlsx'

# Проходим по всем папкам в текущей директории
for folder in current_folder.iterdir():
    if folder.is_dir() and folder.name != 'ВОР':  # Проверяем, что это папка и не папка ВОР
        # Определяем путь к папке ВОР
        vor_folder = folder / 'ВОР'

        if vor_folder.exists() and vor_folder.is_dir():  # Проверяем, что папка ВОР существует
            new_file_name = f'Спецификация_{folder.name.split("-")[-1]}.xlsx'  # Извлекаем часть имени
            new_file_path = vor_folder / new_file_name

            # Проверяем, существует ли файл
            if not new_file_path.exists():
                # Копируем файл
                shutil.copy(template_file, new_file_path)
                print(f'Скопирован: {new_file_path}')
            else:
                print(f'Файл уже существует: {new_file_path}, пропускаем.')
