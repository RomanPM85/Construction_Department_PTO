import os
import requests
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Spacer, Preformatted
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

EXCLUDE_DIRS = {'.venv', 'venv', '__pycache__', '.git', '.idea', '.vscode', 'build', 'dist'}


def register_cyrillic_font():
    """Находит или скачивает чистый моноширинный шрифт для копирования без багов."""
    font_name = "CleanCourier"
    possible_paths = [
        "C:\\Windows\\Fonts\\cour.ttf",  # Windows
        "/System/Library/Fonts/Supplemental/Courier New.ttf",  # macOS
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"  # Linux
    ]
    for path in possible_paths:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(font_name, path))
                return font_name
            except Exception:
                continue

    # Резервный проверенный шрифт, если системные недоступны
    fallback_font_path = os.path.join(os.getcwd(), "DejaVuSansMono.ttf")
    if not os.path.exists(fallback_font_path):
        print("Скачиваю надежный шрифт с поддержкой кириллицы...")
        url = "https://github.com"
        try:
            response = requests.get(url, timeout=15)
            with open(fallback_font_path, "wb") as f:
                f.write(response.content)
        except Exception as e:
            print(f"Не удалось скачать шрифт. Ошибка: {e}")
            return "Courier"
    try:
        pdfmetrics.registerFont(TTFont(font_name, fallback_font_path))
        return font_name
    except Exception:
        return "Courier"


def py_to_pdf(file_path, output_pdf_path, font_name):
    """Конвертирует .py в чистый PDF идеальный для копирования и AI-анализа."""
    file_name = os.path.basename(file_path)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code_content = f.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='windows-1251') as f:
                code_content = f.read()
        except Exception as e:
            print(f"Не удалось прочитать файл {file_name}: {e}")
            return

    # Задаем альбомную ориентацию A4 для максимальной ширины строк (около 145 символов)
    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=landscape(A4),
        rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30
    )

    styles = getSampleStyleSheet()

    # Используем Preformatted: он сохраняет все пробелы, табы и структуру 1-в-1
    code_style = ParagraphStyle(
        'CleanCodeStyle',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=8.5,  # Компактный размер для предотвращения случайных переносов
        leading=11,
    )

    # Мета-данные в начале файла (закомментированы, чтобы не ломать код при копировании всего PDF)
    header_text = f"# ==========================================\n# Source Code: {file_name}\n# ==========================================\n\n"
    full_text_content = header_text + code_content

    # Стандартный Preformatted гарантирует идеальное извлечение текста программами
    story = [Preformatted(full_text_content, code_style)]

    try:
        doc.build(story)
        print(f"Успешно создано: {output_pdf_path}")
    except Exception as e:
        print(f"Ошибка при генерации PDF для {file_name}: {e}")


def main():
    target_dir = input("Введите полный путь к папке для сканирования: ").strip()
    if not os.path.exists(target_dir) or not os.path.isdir(target_dir):
        print("Указанный путь не существует или не является папкой.")
        return

    print("\nВыберите режим сохранения PDF файлов:")
    print("1 — Сохранять в тех же папках, где лежат исходные .py файлы")
    print("2 — Создать отдельную папку и полностью скопировать структуру папок")
    choice = input("Ваш выбор (1 или 2): ").strip()

    output_dir = None
    if choice == '2':
        output_dir = input("Введите путь к новой папке для PDF: ").strip()
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
                print(f"Создана базовая папка для результатов: {output_dir}")
            except Exception as e:
                print(f"Не удалось создать папку: {e}")
                return

    font_name = register_cyrillic_font()

    py_files = []
    for root, dirs, files in os.walk(target_dir):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for file in files:
            if file.endswith('.py'):
                py_files.append(os.path.join(root, file))

    if not py_files:
        print("В указанной директории файлы .py не найдены.")
        return

    print(f"\nНайдено файлов для конвертации: {len(py_files)}\n")

    for file_path in py_files:
        if choice == '1':
            pure_name = os.path.splitext(os.path.basename(file_path))[0]
            output_pdf_path = os.path.join(os.path.dirname(file_path), f"{pure_name}.pdf")
        else:
            rel_path = os.path.relpath(file_path, target_dir)
            pure_rel_path = os.path.splitext(rel_path)[0]
            output_pdf_path = os.path.join(output_dir, f"{pure_rel_path}.pdf")
            os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)

        py_to_pdf(file_path, output_pdf_path, font_name)

    print("\nВсе процессы успешно завершены.")


if __name__ == "__main__":
    main()
