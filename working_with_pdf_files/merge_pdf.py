import os
from PyPDF2 import PdfMerger

# Получаем список всех PDF-файлов в текущей папке
pdf_files = [f for f in os.listdir() if f.endswith('.pdf')]

if not pdf_files:
    print("В текущей папке нет PDF-файлов.")
else:
   # Создаем объект PdfMerger
    merger = PdfMerger()

   # Добавляем каждый PDF-файл в merger
    for pdf in pdf_files:
        merger.append(pdf)

   # Предлагаем название для выходного файла
    output_filename = "merge_pdf_files.pdf"

   # Сохраняем объединенный PDF-файл
    merger.write(output_filename)
    merger.close()

    print(f"PDF-файлы объединены в файл: {output_filename}")
