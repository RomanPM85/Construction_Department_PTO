from pathlib import Path
from PIL import Image

def convert_images_to_pdf(name_file):
    path = Path.cwd()
    # Ищем все jpg, jpeg и png файлы
    image_files = list(path.glob('**/*.jp*g')) + list(path.glob('**/*.png'))
    image_files.sort()  # Опционально: сортируем список файлов

    images = []
    for img_path in image_files:
        img = Image.open(img_path)
        # Конвертируем в RGB, т.к. PDF поддерживает только RGB или L
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        images.append(img)

    if images:
        # Сохраняем первый и добавляем остальные как страницы
        images[0].save(name_file, save_all=True, append_images=images[1:])
        print(f"PDF создан: {name_file}")
    else:
        print("Изображения не найдены.")

if __name__ == "__main__":
    name_create_pdf = input("Введите имя создаваемого файла => ")
    convert_images_to_pdf(name_create_pdf + '.pdf')
