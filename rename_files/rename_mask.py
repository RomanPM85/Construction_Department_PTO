import os
import re


def rename_files_by_mask(directory, mask, new_name_pattern):
    """
    Переименовывает файлы в указанной директории, соответствующие маске,
    используя заданный шаблон нового имени.

    Args:
        directory: Путь к директории.
        mask: Маска для выбора файлов (регулярное выражение).
        new_name_pattern: Шаблон нового имени файла.  В шаблоне можно использовать
                          группы, захваченные из маски, с помощью \1, \2 и т.д.
    """

    try:
        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)

            if os.path.isfile(filepath):
                match = re.search(mask, filename)

                if match:
                    try:
                        new_filename = re.sub(mask, new_name_pattern, filename) # Более безопасный способ подстановки
                        new_filepath = os.path.join(directory, new_filename)

                        if new_filepath != filepath: # Проверка, чтобы не переименовывать файл в то же имя
                            os.rename(filepath, new_filepath)
                            print(f"Файл '{filename}' переименован в '{new_filename}'")
                        else:
                            print(f"Файл '{filename}' соответствует шаблону переименования и не был переименован.")


                    except Exception as e:
                        print(f"Ошибка при переименовании файла '{filename}': {e}")

    except FileNotFoundError:
        print(f"Ошибка: Директория '{directory}' не найдена.")
    except Exception as e:
        print(f"Произошла общая ошибка: {e}")


# --- Пример использования ---

directory_to_rename = "."  # Текущая директория.  Замените на путь к нужной директории, если нужно.
file_mask = r"^(IMG_)(\d+)(.JPG)$" # Маска для выбора файлов, пример: IMG_1234.JPG
new_filename_template = r"image_\2.jpg" # Шаблон нового имени, использующий группу \2 из маски.  Станет image_1234.jpg

rename_files_by_mask(directory_to_rename, file_mask, new_filename_template)
