from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO


def create_watermark(text):
    """Создает PDF с водяным знаком."""
    packet = BytesIO()
    can = canvas.Canvas(packet, pagesize=A4)
    can.setFont("Helvetica", 50)
    can.setFillColorRGB(0.5, 0.5, 0.5, alpha=0.5)  # Серый цвет с прозрачностью
    can.rotate(45)  # Поворот текста на 45 градусов
    can.drawString(200, 100, text)  # Позиция текста
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
    input_pdf = "input.pdf"
    output_pdf = "output.pdf"
    watermark_text = "Confidential"

    watermark = create_watermark(watermark_text)
    add_watermark(input_pdf, output_pdf, watermark)

    print(f"Водяной знак успешно наложен. Результат сохранен в {output_pdf}")
