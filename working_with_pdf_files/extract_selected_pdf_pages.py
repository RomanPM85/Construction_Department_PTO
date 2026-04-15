from pdfrw import PdfReader, PdfWriter
from pathlib import Path
import sys


def parse_page_spec(page_spec):
    """
    Парсит спецификацию страницы: число или строка вида 'start-end'.
    Возвращает список номеров страниц (начиная с 1).
    """
    if isinstance(page_spec, int):
        return [page_spec]
    elif isinstance(page_spec, str) and '-' in page_spec:
        try:
            start, end = map(int, page_spec.split('-'))
            if start > end:
                raise ValueError(f"Некорректный диапазон: {page_spec}. Начало диапазона больше конца.")
            return list(range(start, end + 1))
        except ValueError:
            raise ValueError(f"Некорректный формат диапазона: {page_spec}. Ожидаемый формат: 'start-end'")
    else:
        raise ValueError(f"Некорректная спецификация страницы: {page_spec}")



def extract_pdf_pages(pdf_files, output_folder="extracted_pages"):
    """
    Извлекает указанные страницы из PDF‑файлов.

    Args:
        pdf_files (list): Список кортежей (путь_к_файлу, список_страниц).
            Список страниц может содержать числа и строки вида 'start-end'.
        output_folder (str): Папка для сохранения результатов.
    """
    # Создаём папку для результатов
    output_path = Path(output_folder)
    output_path.mkdir(exist_ok=True)

    for pdf_path, page_specs in pdf_files:
        try:
            # Проверяем существование файла
            if not Path(pdf_path).exists():
                print(f"Файл не найден: {pdf_path}")
                continue

            input_pdf = PdfReader(pdf_path)
            pdf_writer = PdfWriter()

            # Парсим все спецификации страниц в единый список номеров
            all_page_numbers = []
            for spec in page_specs:
                all_page_numbers.extend(parse_page_spec(spec))

            for page_num in all_page_numbers:
                # Преобразуем номер страницы (начиная с 1) в индекс (начиная с 0)
                idx = page_num - 1

                # Проверяем, что индекс страницы существует
                if idx < 0 or idx >= len(input_pdf.pages):
                    print(f"Страница {page_num} не существует в файле {pdf_path}")
                    continue
                pdf_writer.addPage(input_pdf.pages[idx])

            # Формируем имя файла для вывода
            base_name = Path(pdf_path).stem  # Имя файла без расширения
            output_file = output_path / f"{base_name}_extracted.pdf"

            # Сохраняем результат
            pdf_writer.write(output_file)
            print(f"Извлечено: {output_file}")

        except Exception as e:
            print(f"Ошибка при обработке файла {pdf_path}: {e}")

    print(f"Все страницы обработаны. Результаты сохранены в папку '{output_folder}'.")



if __name__ == "__main__":
    # Пример использования (можно заменить на свои данные)
    sample_files = [
        ("example1.pdf", [25, 26]),
        ("example2.pdf", ["135-183"]),
        ("example3.pdf", [5, 6]),
        ("example4.pdf", [7]),
        ("example5.pdf", [25, 26, 27, 28, 29]),
        ("example6.pdf", [9, 10, 11]),
    ]

    extract_pdf_pages(sample_files)
