import PyPDF2


def parse_page_ranges(page_ranges):
    pages = []
    for page_range in page_ranges:
        if '-' in page_range:
            start, end = map(int, page_range.split('-'))
            pages.extend(range(start, end + 1))  # Добавляем диапазон страниц
        else:
            pages.append(int(page_range))  # Добавляем отдельную страницу
    return pages


def split_pdf(input_pdf, page_requests, output_files):
    # Открываем исходный PDF файл
    with open(input_pdf, 'rb') as file:
        reader = PyPDF2.PdfReader(file)

        for page_request, output_file in zip(page_requests, output_files):
            # Создаем новый PDF файл для записи
            writer = PyPDF2.PdfWriter()

            for page_info in page_request:
                if isinstance(page_info, tuple):
                    page_numbers, rotation = page_info
                else:
                    page_numbers, rotation = [page_info], 0  # По умолчанию без поворота

                # Парсим запрашиваемые страницы
                pages_to_extract = parse_page_ranges(page_numbers)

                for page_number in pages_to_extract:
                    # Поворачиваем страницу и добавляем в новый документ
                    page = reader.pages[page_number - 1]
                    page.rotate(rotation)  # Поворачиваем страницу на указанный угол
                    writer.add_page(page)

            # Записываем новый PDF файл
            with open(output_file, 'wb') as output:
                writer.write(output)
            print(f"Создан файл: {output_file}")


if __name__ == "__main__":
    input_pdf = "File.pdf"

    # Указываем страницы для извлечения и названия выходных файлов
    page_requests = [
        [(["1", "2"], 270), (["5-7"], 0)],  # Страницы для первого файла (1, 2 с поворотом 270°, 5, 6, 7 без поворота)
        [(["3-4"], 180), (["8"], 0)],  # Страницы для второго файла (3, 4 с поворотом 180°, 8 без поворота)
        # Добавьте другие списки страниц по мере необходимости
    ]

    output_files = [
        "файл_1.pdf",  # Название первого выходного файла
        "файл_2.pdf",  # Название второго выходного файла
        # Добавьте другие названия по мере необходимости
    ]

    # Вызываем функцию для разбивки PDF
    split_pdf(input_pdf, page_requests, output_files)
