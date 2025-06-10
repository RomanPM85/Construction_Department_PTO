from pathlib import Path
import PyPDF2

def extract_pdf_pages():
    # Запрашиваем у пользователя имя файла
    input_file_name = input("Введите имя PDF файла (с расширением): ")
    input_path = Path(input_file_name)

    # Проверяем, существует ли файл
    if not input_path.is_file():
        print(f"Файл {input_path} не найден.")
        return

    # Запрашиваем номера страниц для извлечения
    pages_input = input("Введите номера страниц для извлечения (через запятую): ")
    pages_to_extract = [int(page.strip()) - 1 for page in pages_input.split(',') if page.strip().isdigit()]

    # Создаем новый PDF файл для сохранения извлеченных страниц
    output_pdf = PyPDF2.PdfWriter()

    # Открываем исходный PDF файл
    with open(input_path, 'rb') as input_pdf_file:
        reader = PyPDF2.PdfReader(input_pdf_file)

        # Извлекаем указанные страницы
        for page_number in pages_to_extract:
            if 0 <= page_number < len(reader.pages):
                output_pdf.add_page(reader.pages[page_number])
            else:
                print(f"Страница {page_number + 1} вне диапазона.")

    # Формируем имя выходного файла без фигурных скобок
    extracted_pages = '_'.join(str(p + 1) for p in pages_to_extract)  # Номера страниц без фигурных скобок
    output_file_name = f"{input_path.stem}_page_{extracted_pages}.pdf"
    output_path = input_path.parent / output_file_name

    # Сохраняем извлеченные страницы в новый файл
    with open(output_path, 'wb') as output_pdf_file:
        output_pdf.write(output_pdf_file)

    print(f"Извлеченные страницы сохранены в: {output_path}")

if __name__ == "__main__":
    extract_pdf_pages()
