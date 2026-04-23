from pdfrw import PdfReader, PdfWriter
from pathlib import Path


def parse_page_spec(page_spec):
    """Парсит элемент списка страниц: число → [число], строка 'N-M' → [N, ..., M]."""
    if isinstance(page_spec, int):
        return [page_spec]
    elif isinstance(page_spec, str) and '-' in page_spec:
        start, end = map(int, page_spec.split('-'))
        if start > end:
            raise ValueError(f"Некорректный диапазон: {page_spec}")
        return list(range(start, end + 1))
    else:
        raise ValueError(f"Неподдерживаемый формат: {page_spec}")


def expand_page_list(page_list):
    """Преобразует список спецификаций в отсортированный список уникальных номеров страниц."""
    result = set()
    for spec in page_list:
        result.update(parse_page_spec(spec))
    return sorted(result)

def extract_pdf_pages(pdf_files, output_folder_name):
    """Извлекает указанные страницы из PDF‑файлов в заданную папку."""
    output_folder = Path(output_folder_name)
    output_folder.mkdir(exist_ok=True)

    for pdf_path, page_specs in pdf_files:
        try:
            if not Path(pdf_path).exists():
                print(f"Файл не найден: {pdf_path}")
                continue

            input_pdf = PdfReader(pdf_path)
            pdf_writer = PdfWriter()
            total_pages = len(input_pdf.pages)

            page_numbers = expand_page_list(page_specs)
            valid_pages_extracted = False

            for page_num in page_numbers:
                idx = page_num - 1
                if idx < 0 or idx >= total_pages:
                    print(f"Страница {page_num} не существует в {pdf_path} (всего: {total_pages})")
                    continue

                pdf_writer.addPage(input_pdf.pages[idx])
                valid_pages_extracted = True

            if valid_pages_extracted:
                base_name = Path(pdf_path).stem
                output_path = output_folder / f"{base_name}_ведомость.pdf"
                pdf_writer.write(output_path)
                print(f"Извлечено: {output_path}")
            else:
                print(f"Для {pdf_path} не найдено валидных страниц.")

        except Exception as e:
            print(f"Ошибка при обработке {pdf_path}: {e}")

    print(f"Обработка завершена. Результаты в папке '{output_folder_name}'.")

if __name__ == "__main__":
    # Конфигурация
    OUTPUT_FOLDER = "extracted_pages"
    PDF_FILES = [
        ("файл1.pdf", ["82-83"]),
        # Добавьте другие файлы по необходимости:
        ("файл2.pdf", [1, "5-7", 10]),
    ]

    extract_pdf_pages(PDF_FILES, OUTPUT_FOLDER)
