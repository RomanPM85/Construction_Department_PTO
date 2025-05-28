from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import io


def create_page_number_pdf(num_pages):
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)

    # Регистрация шрифта, поддерживающего кириллицу
    pdfmetrics.registerFont(TTFont('Arial', 'Arial.ttf'))  # Убедитесь, что файл Arial.ttf доступен
    can.setFont('Arial', 8)

    for i in range(num_pages):
        # Установите позицию для номера страницы (нижний правый угол)
        can.drawString(500, 20, f"page {i + 1}")
        can.showPage()

    can.save()
    packet.seek(0)
    return PdfReader(packet)


def add_page_numbers(input_pdf_path, output_pdf_path):
    reader = PdfReader(input_pdf_path)
    writer = PdfWriter()

    total_pages = len(reader.pages)

    # Создаем PDF с номерами страниц, начиная с 1 для третьей страницы
    page_number_pdf = create_page_number_pdf(total_pages - 2)  # Создаем PDF для страниц с 3 по конец

    for i in range(total_pages):
        page = reader.pages[i]
        if i >= 2:  # Нумеруем начиная с третьей страницы (индекс 2)
            # Получаем соответствующую страницу с номером
            number_page = page_number_pdf.pages[i - 2]
            # Объединяем номер страницы с оригинальной страницей
            page.merge_page(number_page)
        writer.add_page(page)

    with open(output_pdf_path, "wb") as output_pdf:
        writer.write(output_pdf)


# Использование функции
add_page_numbers("ИД_КР_2025.05.28.pdf", "output.pdf")
