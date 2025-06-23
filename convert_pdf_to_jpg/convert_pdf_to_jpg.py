# import module
import os
import shutil
import time
import jpg2pdf
from pathlib import Path

from pdf2image import convert_from_path


def convert_pdf_to_jpg(self_file, dir_jpg):
    # Store Pdf with convert_from_path function
    output_folder = Path.cwd()
    images = convert_from_path(self_file)
    if not os.path.isdir(dir_jpg):
        os.mkdir(dir_jpg)
    for i in range(len(images)):
        # Save pages as images in the pdf
        name_doc = 'page-' + str(i) + '.jpg'
        images[i].save(output_folder / dir_jpg / name_doc, 'JPEG')


def convert_jpg_to_pdf(folder):
    find_jpg_file = Path.cwd() / folder
    # with jpg2pdf.create('convert_file_jpg_to_pdf.pdf') as pdf:
    with jpg2pdf.create(str(folder)) as pdf:
        list_jpg_files = find_jpg_file.glob('*.jpg')
        for jpg in list_jpg_files:
            pdf.add(jpg, find_jpg_file)


def delete_folder():
    path = '.'
    dirs = os.listdir(path)
    for item in dirs:
        if os.path.isdir(str(item)):
            shutil.rmtree(os.path.join(item))


def create_list_folder(pattern):
    files = Path.cwd().glob(pattern)
    return list(files)


def create_folder(name_dir):
    output_folder = Path.cwd()
    if not os.path.isdir(name_dir):
        os.mkdir(name_dir)
    return output_folder


if __name__ == "__main__":
    start_time = time.time()
    welcome = ("Привет, это программа для получение из pdf файла в jpg страницы. \n"
               f"GNU GPL (GNU General Public License) Mamchiy Roman https://github.com/RomanPM85")

    print(welcome)
    start_script = input(f"Введите номер команды программы=>.\n"
                         f"Если 1, файлы из pdf преобразует в jpg. \n"
                         f"Если 2, файлы jpg преоразует в pdf. \n"
                         f"Если 3, удалит все папки с jpg файлами.\n"
                         f"Если 4, создает папки с именем файлов pdf. \n"
                         f"==>"
                         )

    if start_script == '1':
        # Замена input на список файлов
        pattern_files = [
            '*.pdf',  # Пример: все PDF файлы в текущей директории
            'documents/*.pdf',  # Пример: PDF файлы в поддиректории documents
            # Добавьте сюда нужные пути/шаблоны
        ]

        for pattern_file in pattern_files:
            folders = create_list_folder(pattern_file)
            for i in folders:
                first_name = i.stem
                new_name = first_name.replace(" ", "")
                create_folder(new_name)
                convert_pdf_to_jpg(i, new_name)

    elif start_script == '2':
        input_file = input(f"Введите имя папки месторасположения jpg файлов: ")
        convert_jpg_to_pdf(input_file)
    elif start_script == '3':
        delete_folder()
    elif start_script == '4':
        folders = create_list_folder('*.pdf')
        for i in folders:
            first_name = i.stem
            new_name = first_name.replace(" ", "")
            create_folder(new_name)

    else:
        print(f"Код введен неверно")
    print("--- %s seconds ---" % (time.time() - start_time))
