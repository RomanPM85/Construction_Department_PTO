import os
import requests
import tokenize
import io
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Preformatted
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

EXCLUDE_DIRS = {'.venv', 'venv', '__pycache__', '.git', '.idea', '.vscode', 'build', 'dist'}


def wrap_long_strings_in_code(code_text, max_len=110):
    """
    Использует модуль tokenize для поиска сверхдлинных строк
    и их безопасного разбиения на синтаксически корректный многострочный Python-текст.
    """
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(code_text).readline))
    except Exception:
        # Если код имеет синтаксические ошибки, возвращаем как есть, чтобы не сломать логику
        return code_text

    string_tokens = [t for t in tokens if t.type == tokenize.STRING]
    lines = code_text.splitlines(keepends=True)

    # Обрабатываем токены с конца файла к началу, чтобы индексы строк/символов не съезжали
    for token in reversed(string_tokens):
        s_val = token.string

        # Пропускаем многострочные комментарии/docstrings (они уже оформлены через ''' или """)
        if s_val.startswith(('"""', "'''")):
            continue

        start_line, start_col = token.start
        end_line, end_col = token.end

        # Если строка целиком длиннее лимита
        if start_col + len(s_val) > max_len and len(s_val) > 20:
            # Определяем тип кавычек и префиксы (r, f, b)
            quote_char = '"' if s_val.endswith('"') else "'"
            prefix = ""
            for char in ['r', 'R', 'f', 'F', 'b', 'B']:
                if s_val.startswith(char):
                    prefix += char

            # Извлекаем чистый контент строки без внешних кавычек и префиксов
            content = s_val[len(prefix) + 1: -1]

            # Вычисляем размер чанков для нарезки текста
            chunk_size = max(20, max_len - start_col - len(prefix) - 5)
            chunks = [content[i:i + chunk_size] for i in range(0, len(content), chunk_size)]

            if len(chunks) <= 1:
                continue

            # Получаем отступ текущей строки
            orig_line = lines[start_line - 1]
            indent = orig_line[:len(orig_line) - len(orig_line.lstrip())]
            extra_indent = indent + "    "

            # Собираем красивую и синтаксически верную структуру неявного объединения строк в Python
            new_text_lines = []
            new_text_lines.append(f"(\n{extra_indent}{prefix}{quote_char}{chunks[0]}{quote_char}")
            for chunk in chunks[1:]:
                new_text_lines.append(f"{extra_indent}{prefix}{quote_char}{chunk}{quote_char}")
            new_text_lines[-1] += f"\n{indent})"

            new_string_repr = "\n".join(new_text_lines)

            # Заменяем старую строку в кодовой базе (работает для однострочных литералов)
            if start_line == end_line:
                target_line = lines[start_line - 1]
                replaced = target_line[:start_col] + new_string_repr + target_line[end_col:]
                lines[start_line - 1] = replaced

    return "".join(lines)


def register_cyrillic_font():
    """Находит или скачивает моноширинный шрифт с поддержкой кириллицы."""
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
    """Конвертирует .py в PDF с умным переносом строк без разрывов синтаксиса."""
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

    # 1. Сначала обрабатываем сверхдлинные строки силами токенайзера
    processed_code = wrap_long_strings_in_code(code_content, max_len=120)

    # 2. Настраиваем широкий ландшафтный документ
    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=landscape(A4),
        rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30
    )

    styles = getSampleStyleSheet()
    code_style = ParagraphStyle(
        'CleanCodeStyle',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=8.5,
        leading=11,  # Межстрочный интервал
    )

    story = []

    # Добавляем безопасную шапку
    story.append(Preformatted("# ==========================================", code_style))
    story.append(Preformatted(f"# Source Code: {file_name}", code_style))
    story.append(Preformatted("# ==========================================\n", code_style))

    # 🌟 ГЛАВНОЕ ИСПРАВЛЕНИЕ: Разбиваем код посимвольно на строки
    # и каждую строку пускаем отдельным элементом в story.
    # Это заставит ReportLab переносить страницы ровно МЕЖДУ строками.
    for line in processed_code.splitlines():
        # Если в коде есть пустая строка, сохраняем её для читаемости
        if not line.strip():
            story.append(Preformatted("", code_style))
        else:
            story.append(Preformatted(line, code_style))

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
