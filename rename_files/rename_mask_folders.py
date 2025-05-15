import os

# Параметры для замены
old_substring = "-Р-"  # Замените на текст, который нужно изменить
new_substring = "-ИД-"  # Замените на новый текст

# Получаем список папок в текущей директории
current_dir = os.getcwd()
folders = [f for f in os.listdir(current_dir) if os.path.isdir(os.path.join(current_dir, f))]

# Переименовываем папки
for folder in folders:
    if old_substring in folder:
        new_name = folder.replace(old_substring, new_substring)

        # Проверяем, не существует ли уже папка с новым именем
        if not os.path.exists(os.path.join(current_dir, new_name)):
            os.rename(
                os.path.join(current_dir, folder),
                os.path.join(current_dir, new_name)
            )
            print(f"Переименовано: {folder} -> {new_name}")
        else:
            print(f"Ошибка: {new_name} уже существует")
