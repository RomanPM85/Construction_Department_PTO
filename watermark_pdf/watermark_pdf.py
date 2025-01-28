from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from io import BytesIO


def create_watermark(image_path):
    """Создает PDF с водяным знаком из изображения."""
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=A4)

    # Загрузка изображения
    img = ImageReader(image_path)

    # Размеры страницы
    width, height = A4

    # Наложение изображения (можно настроить размер и положение)
    can.drawImage(img, x=100, y=100, width=width - 200, height=height - 200, mask='auto', preserveAspectRatio=True)
    can.save()

    packet.seek(0)
    return PdfReader(packet)


def add_watermark(input_pdf, output_pdf, watermark):
    """Накладывает водяной знак на каждую страницу PDF."""
    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    watermark_page = watermark.pages[0]

    for i in range(len(reader.pages)):
        page = reader.pages[i]
        page.merge_page(watermark_page)
        writer.add_page(page)

    with open(output_pdf, "wb") as output_pdf_file:
        writer.write(output_pdf_file)


if __name__ == "__main__":
    input_pdf = "input.pdf"  # Исходный PDF-файл
    output_pdf = "output.pdf"  # Выходной PDF-файл с водяным знаком
    watermark_image = "watermark.png"  # Путь к изображению водяного знака

    watermark = create_watermark(watermark_image)
    add_watermark(input_pdf, output_pdf, watermark)

    print(f"Водяной знак успешно наложен. Результат сохранен в {output_pdf}")
