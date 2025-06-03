from pathlib import Path
from PIL import Image
import fitz  # PyMuPDF

def main():
    # Пути к файлам
    pdf_path = Path("input.pdf")
    png_path = Path("Piramida_TN.png")
    output_pdf_path = Path("output.pdf")

    # Открываем PDF
    pdf_doc = fitz.open(pdf_path)
    page = pdf_doc[0]  # Работаем с первой страницей

    # Размеры PDF страницы в пунктах (1 пункт = 1/72 дюйма, в PyMuPDF 1 пункт = 1 px)
    pdf_width, pdf_height = page.rect.width, page.rect.height
    print(f"Размер PDF страницы: ширина={pdf_width:.0f} px, высота={pdf_height:.0f} px")

    # Открываем PNG
    png_img = Image.open(png_path)
    png_width, png_height = png_img.size
    print(f"Размер PNG изображения: ширина={png_width} px, высота={png_height} px")

    # Запрос максимального размера PNG (по ширине или высоте)
    max_size = int(input("Введите максимальный размер PNG (в px) по ширине или высоте: "))

    # Запрос угла поворота (градусы по часовой стрелке)
    rotation_angle = float(input("Введите угол поворота PNG (в градусах, по часовой стрелке, например 0, 90, 180): "))

    # Вычисляем масштаб, чтобы сохранить пропорции и не превышать max_size
    scale_w = max_size / png_width
    scale_h = max_size / png_height
    scale = min(scale_w, scale_h, 1.0)  # Не увеличиваем изображение, только уменьшаем или оставляем

    new_width = int(png_width * scale)
    new_height = int(png_height * scale)
    print(f"Масштабированный размер PNG до поворота: ширина={new_width} px, высота={new_height} px")

    # Масштабируем PNG
    if scale < 1.0:
        png_img = png_img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Поворачиваем PNG (по часовой стрелке)
    # В PIL поворот против часовой стрелки, поэтому используем отрицательный угол
    png_img = png_img.rotate(-rotation_angle, expand=True)

    # После поворота размеры могут измениться
    rotated_width, rotated_height = png_img.size
    print(f"Размер PNG после поворота: ширина={rotated_width} px, высота={rotated_height} px")

    # Запрос координат расположения PNG на PDF странице (в пикселях от верхнего левого угла)
    x = float(input(f"Введите координату X (0 - {pdf_width - rotated_width}): "))
    y = float(input(f"Введите координату Y (0 - {pdf_height - rotated_height}): "))

    # Сохраняем временно PNG в память
    import io
    img_byte_arr = io.BytesIO()
    png_img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    # Добавляем изображение на PDF
    rect = fitz.Rect(x, y, x + rotated_width, y + rotated_height)
    page.insert_image(rect, stream=img_byte_arr)

    # Сохраняем результат
    pdf_doc.save(output_pdf_path)
    print(f"Результат сохранен в {output_pdf_path}")

if __name__ == "__main__":
    main()
