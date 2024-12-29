import fitz  # PyMuPDF
from PIL import Image
import numpy as np


def remove_background(image):
    # Пример простой обработки: конвертация в черно-белый и удаление белого фона
    image = image.convert("L")  # Конвертируем в черно-белый
    np_image = np.array(image)

    # Убираем белый фон
    np_image[np_image > 200] = 255  # Условие для удаления фона
    np_image[np_image <= 200] = 0  # Применяем черный цвет к остальным пикселям

    return Image.fromarray(np_image)


def process_pdf(input_pdf, output_pdf):
    doc = fitz.open(input_pdf)
    new_doc = fitz.open()  # Создаем новый PDF документ

    for page in doc:
        pix = page.get_pixmap()  # Получаем изображение страницы
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # Убираем фон
        processed_img = remove_background(img)

        # Сохраняем обработанное изображение в новый PDF
        img_bytes = processed_img.tobytes("jpeg")
        img_page = new_doc.new_page(width=pix.width, height=pix.height)
        img_page.insert_image(img_page.rect, stream=img_bytes)

    new_doc.save(output_pdf)
    new_doc.close()
    doc.close()


# Пример использования

if __name__ == "__main__":
    process_pdf("input.pdf", "output.pdf")
