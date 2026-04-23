from pdfrw import PdfReader, PdfWriter
from pathlib import Path
import re
import logging
from datetime import datetime


# Настройка логирования
def setup_logging():
    """Настраивает логирование в файл и консоль."""
    log_filename = f"pdf_extractor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger()


def parse_page_spec(page_spec):
    """Парсит элемент списка страниц: число → [число], строка 'N(суффикс)' или 'N-M(суффикс)' → [N/N..M] + суффикс."""
    if isinstance(page_spec, int):
        return [page_spec], None
    elif isinstance(page_spec, str):
        # Паттерн для N-M(суффикс)
        range_match = re.match(r'^(\d+)-(\d+)\(([^)]+)\)$', page_spec)
        if range_match:
            start, end, suffix = int(range_match.group(1)), int(range_match.group(2)), range_match.group(3)
            if start > end:
                raise ValueError(f"Некорректный диапазон: {page_spec} (начало > конца)")
            return list(range(start, end + 1)), suffix

        # Паттерн для N(суффикс) — одиночная страница с суффиксом
        single_match = re.match(r'^(\d+)\(([^)]+)\)$', page_spec)
        if single_match:
            page_num, suffix = int(single_match.group(1)), single_match.group(2)
            return [page_num], suffix

        # Просто диапазон без суффикса
        elif '-' in page_spec:
            start, end = map(int, page_spec.split('-'))
            if start > end:
                raise ValueError(f"Некорректный диапазон: {page_spec}")
            return list(range(start, end + 1)), None

        else:
            raise ValueError(f"Неподдерживаемый формат: {page_spec}")
    else:
        raise ValueError(f"Неподдерживаемый формат страницы: {page_spec}")


def extract_pdf_pages(pdf_files, output_folder_name):
    """Извлекает указанные страницы из PDF‑файлов в заданную папку, создавая отдельные файлы для каждого суффикса."""
    logger = logging.getLogger()
    output_folder = Path(output_folder_name)
    output_folder.mkdir(exist_ok=True)

    total_files_processed = 0
    total_pages_extracted = 0

    for pdf_path, page_specs in pdf_files:
        try:
            if not Path(pdf_path).exists():
                logger.warning(f"Файл не найден: {pdf_path}")
                continue

            input_pdf = PdfReader(pdf_path)
            total_pages = len(input_pdf.pages)
            base_name = Path(pdf_path).stem
            logger.info(f"Обрабатывается файл: {pdf_path} (всего страниц: {total_pages})")

            # Группируем страницы по суффиксам
            suffix_groups = {}
            for spec in page_specs:
                try:
                    pages, suffix = parse_page_spec(spec)
                    if suffix is None:
                        # Страницы без суффикса — помещаем в специальную группу
                        suffix = 'без_суффикса'
                    if suffix not in suffix_groups:
                        suffix_groups[suffix] = set()
                    suffix_groups[suffix].update(pages)
                except ValueError as e:
                    logger.error(f"Ошибка парсинга спецификации '{spec}' для файла {pdf_path}: {e}")
                    continue

            # Обрабатываем каждую группу отдельно
            for suffix, page_numbers in suffix_groups.items():
                pdf_writer = PdfWriter()
                valid_pages_extracted = False
                extracted_pages_count = 0

                for page_num in sorted(page_numbers):
                    idx = page_num - 1
                    if idx < 0 or idx >= total_pages:
                        logger.warning(f"Страница {page_num} не существует в {pdf_path} (всего: {total_pages})")
                        continue

                    pdf_writer.addPage(input_pdf.pages[idx])
                    valid_pages_extracted = True
                    extracted_pages_count += 1

                if valid_pages_extracted:
                    output_path = output_folder / f"{base_name}_ведомость_{suffix}.pdf"
                    pdf_writer.write(output_path)
                    logger.info(f"Извлечено: {output_path} ({extracted_pages_count} страниц)")
                    total_pages_extracted += extracted_pages_count
                else:
                    logger.warning(f"Для суффикса '{suffix}' в файле {pdf_path} не найдено валидных страниц.")

            total_files_processed += 1

        except Exception as e:
            logger.error(f"Критическая ошибка при обработке {pdf_path}: {e}")

    logger.info(f"Обработка завершена. Обработано файлов: {total_files_processed}, извлечено страниц: {total_pages_extracted}")
    logger.info(f"Результаты в папке: '{output_folder_name}'")


if __name__ == "__main__":
    # Настройка логирования перед запуском
    logger = setup_logging()
    logger.info("Запуск извлечения страниц из PDF-файлов")

    OUTPUT_FOLDER = "extracted_pages"
    # ЗАМЕНИТЕ ЭТИ ДАННЫЕ НА ВАШИ ФАЙЛЫ И СПЕЦИФИКАЦИИ СТРАНИЦ
    PDF_FILES = [
        ("файл1.pdf", ["10-15(суффикс1)", "42(суффикс2)"]),
        ("файл2.pdf", ["24(суффикс1)", "33(суффикс3)"]),
        ("файл3.pdf", ["5-7(суффикс2)", "100(суффикс1)"]),
    ]

    extract_pdf_pages(PDF_FILES, OUTPUT_FOLDER)