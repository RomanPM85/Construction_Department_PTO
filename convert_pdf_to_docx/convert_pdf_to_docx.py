from pdf2docx import Converter
import os


def convert_pdf_to_docx(pdf_path, docx_path):
    try:
        cv = Converter(pdf_path)
        cv.convert(docx_path)
        cv.close()
        print(f"Файл {pdf_path} успешно конвертирован в {docx_path}")
        return True
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        return False


# Пример использования
pdf_file_path = "pdf_file.pdf"  # Путь к исходному файлу
docx_file_path = "your_file.docx"  # Путь к выходному файлу

if convert_pdf_to_docx(pdf_file_path, docx_file_path):
    print("PDF конвертирован")
else:
    print("Не удалось конвертировать PDF")
