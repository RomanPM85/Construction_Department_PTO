import os
from pathlib import Path
from PIL import Image

def resize_images():
    # Получаем текущую папку
    current_folder = Path('.')

    # Получаем список всех jpg файлов в текущей папке
    jpg_files = list(current_folder.glob('*.jpg'))

    # Если нет jpg файлов, выходим
    if not jpg_files:
        print("Нет jpg файлов в текущей папке.")
        return

    # Определяем размеры изображений
    sizes = []
    for file in jpg_files:
        with Image.open(file) as img:
            sizes.append(img.size)

    # Вычисляем средние размеры
    average_width = sum(size[0] for size in sizes) // len(sizes)
    average_height = sum(size[1] for size in sizes) // len(sizes)

    # Создаем папку для сохранения измененных изображений, если её нет
    output_folder = current_folder / 'jpg_convert'
    output_folder.mkdir(exist_ok=True)

    # Открываем лог-файл для записи
    log_file_path = current_folder / 'resize_log.txt'
    with open(log_file_path, 'w') as log_file:
        log_file.write("Файл; Размер до изменения (Ширина x Высота); Размер после изменения (Ширина x Высота)\n")

        # Изменяем размеры изображений и сохраняем их
        for file in jpg_files:
            with Image.open(file) as img:
                original_size = img.size
                # Изменяем размер изображения, сохраняя соотношение сторон
                img.thumbnail((average_width, average_height))
                # Сохраняем измененное изображение в новую папку
                img.save(output_folder / file.name)

                # Записываем информацию в лог-файл
                new_size = img.size
                log_file.write(f"{file.name}; {original_size[0]} x {original_size[1]}; {new_size[0]} x {new_size[1]}\n")

    print(f"Изображения успешно изменены и сохранены в папке '{output_folder}'. Лог записан в '{log_file_path}'.")

if __name__ == "__main__":
    resize_images()
