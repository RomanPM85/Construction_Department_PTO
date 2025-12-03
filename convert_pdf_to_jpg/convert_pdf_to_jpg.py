import os
import shutil
import time
import jpg2pdf
from pathlib import Path
from pdf2image import convert_from_path


def convert_pdf_to_jpg(pdf_file: Path, output_dir: Path):
    print(f"Конвертация PDF в JPG: {pdf_file} -> {output_dir}")
    images = convert_from_path(str(pdf_file))
    output_dir.mkdir(exist_ok=True)
    for i, image in enumerate(images):
        name_doc = f'page-{i}.jpg'
        image_path = output_dir / name_doc
        image.save(image_path, 'JPEG')
        print(f"  Сохранена страница {i + 1}/{len(images)}: {image_path}")
    print(f"Завершено конвертирование {pdf_file.name} в JPG.\n")


def convert_jpg_to_pdf(folder: Path):
    print(f"Конвертация JPG в PDF из папки: {folder}")
    if not folder.is_dir():
        print(f"Ошибка: Папка {folder} не существует.")
        return
    output_pdf = folder.with_suffix('.pdf')
    with jpg2pdf.create(str(output_pdf)) as pdf:
        jpg_files = sorted(folder.glob('*.jpg'))
        if not jpg_files:
            print(f"В папке {folder} нет JPG файлов.")
            return
        for jpg in jpg_files:
            pdf.add(jpg, folder)
            print(f"  Добавлен файл {jpg.name}")
    print(f"PDF создан: {output_pdf}\n")


def delete_folders_with_jpg():
    print("Удаление всех папок, содержащих JPG файлы в текущей директории...")
    cwd = Path.cwd()
    deleted_count = 0
    for item in cwd.iterdir():
        if item.is_dir():
            jpg_files = list(item.glob('*.jpg'))
            if jpg_files:
                shutil.rmtree(item)
                print(f"  Удалена папка: {item}")
                deleted_count += 1
    if deleted_count == 0:
        print("Папок с JPG файлами для удаления не найдено.")
    else:
        print(f"Удалено папок: {deleted_count}\n")


def create_folders_for_pdfs(pattern='*.pdf'):
    print(f"Создание папок для PDF файлов по шаблону '{pattern}'...")
    pdf_files = list(Path.cwd().glob(pattern))
    if not pdf_files:
        print("PDF файлы не найдены.")
        return
    for pdf_file in pdf_files:
        folder_name = pdf_file.stem.replace(" ", "")
        folder_path = Path.cwd() / folder_name
        folder_path.mkdir(exist_ok=True)
        print(f"  Создана папка: {folder_path}")
    print("Завершено создание папок.\n")


def main():
    start_time = time.time()
    welcome = (
        "Привет, это программа для получения из PDF файла страниц в JPG.\n"
        "GNU GPL (GNU General Public License) Mamchiy Roman https://github.com/RomanPM85"
    )
    print(welcome)

    start_script = input(
        "Введите номер команды программы:\n"
        "1 - Конвертировать PDF файлы в JPG\n"
        "2 - Конвертировать JPG файлы в PDF\n"
        "3 - Удалить все папки с JPG файлами\n"
        "4 - Создать папки с именами PDF файлов\n"
        "==> "
    ).strip()

    if start_script == '1':
        pattern_files = [
            '*.pdf',          # Все PDF в текущей директории
            'documents/*.pdf' # PDF в поддиректории documents
        ]
        for pattern_file in pattern_files:
            pdf_files = list(Path.cwd().glob(pattern_file))
            if not pdf_files:
                print(f"Файлы по шаблону '{pattern_file}' не найдены.")
                continue
            for pdf_file in pdf_files:
                folder_name = pdf_file.stem.replace(" ", "")
                output_dir = Path.cwd() / folder_name
                output_dir.mkdir(exist_ok=True)
                convert_pdf_to_jpg(pdf_file, output_dir)

    elif start_script == '2':
        input_folder_name = input("Введите имя папки с JPG файлами: ").strip()
        input_folder = Path.cwd() / input_folder_name
        convert_jpg_to_pdf(input_folder)

    elif start_script == '3':
        delete_folders_with_jpg()

    elif start_script == '4':
        create_folders_for_pdfs()

    else:
        print("Код введен неверно")

    print(f"--- Время выполнения: {time.time() - start_time:.2f} секунд ---")


if __name__ == "__main__":
    main()
