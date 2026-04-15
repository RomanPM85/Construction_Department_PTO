from pathlib import Path
import subprocess
import re

def get_pdf_page_size_mm(pdf_path):
    """
    Получает размер страницы PDF в мм с помощью pdfinfo.
    Возвращает строку вида '210x297' или 'Ошибка' при неудаче.
    """
    try:
        # Запускаем pdfinfo и получаем вывод
        result = subprocess.run(
            ['pdfinfo', str(pdf_path)],
            capture_output=True,
            text=True,
            check=True
        )

        # Ищем строку с размером страницы
        match = re.search(r'Page size:\s*([\d.]+)\s*x\s*([\d.]+)', result.stdout)
        if match:
            width_pts = float(match.group(1))
            height_pts = float(match.group(2))

            # Переводим пункты в мм: 1 pt = 25.4/72 мм
            width_mm = int(round(width_pts * 25.4 / 72))
            height_mm = int(round(height_pts * 25.4 / 72))

            return f"{width_mm}x{height_mm}"
        else:
            return "Ошибка: не найден размер страницы"
    except subprocess.CalledProcessError:
        return "Ошибка: pdfinfo не смог обработать файл"
    except Exception as e:
        return f"Ошибка: {str(e)}"

def main():
    # Текущая папка
    current_dir = Path('.')

    # Находим все PDF-файлы в текущей папке
    pdf_files = list(current_dir.glob('*.pdf'))

    if not pdf_files:
        print("В текущей папке не найдено PDF-файлов.")
        return

    # Список для хранения результатов
    results = []

    print("Обрабатываю PDF-файлы...")
    for pdf_file in pdf_files:
        size_mm = get_pdf_page_size_mm(pdf_file)
        results.append(f"{pdf_file.name} - {size_mm} мм")
        print(f"  {pdf_file.name}: {size_mm} мм")

    # Сохраняем результаты в текстовый файл
    output_file = current_dir / "размеры_pdf.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(results))

    print(f"\nРезультаты сохранены в файл: {output_file}")

if __name__ == "__main__":
    main()
