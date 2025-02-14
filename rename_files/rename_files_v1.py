import os


def rename_files_in_folder(folder_path, old_part, new_part):
    # Рекурсивно обходим все файлы и папки
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            # Проверяем, содержит ли имя файла искомую часть
            if old_part in file:
                # Формируем новое имя файла
                new_file_name = file.replace(old_part, new_part)
                # Получаем полный путь к старому и новому файлу
                old_file_path = os.path.join(root, file)
                new_file_path = os.path.join(root, new_file_name)
                # Переименовываем файл
                os.rename(old_file_path, new_file_path)
                print(f"Переименован: {old_file_path} -> {new_file_path}")


if __name__ == "__main__":
    # Укажите путь к текущей папке
    current_folder = os.getcwd()

    # Укажите часть имени для замены
    old_part = "старая_часть"
    new_part = "новая_часть"

    # Запускаем переименование
    rename_files_in_folder(current_folder, old_part, new_part)
