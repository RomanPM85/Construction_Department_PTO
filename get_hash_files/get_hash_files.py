# -*- coding: utf-8 -*-
import hashlib
from pathlib import Path


def returns_hash_file(file_path):
    """ a function that returns a hash256 file """

    sha256_hash = hashlib.new('sha256')

    with open(file_path, 'rb') as file:
        while True:
            data = file.read(1024)
            if not data:
                break
            sha256_hash.update(data)
        return f'SHA-256:{sha256_hash.hexdigest()},{str(file_path.name)} \n'


def writes_text_file(self):
    """ the function writes data to a file """
    with open("sha256.txt", 'a+', encoding='utf-8') as file:
        file.write(self)


def delete_file(self):
    """ a function that deletes all files """
    Path.unlink(self)
    return self


def iterating_files_folder(files):
    """ a function for calling other functions to iterate through and write the hash of a file """
    for file_item in files:
        writes_text_file(returns_hash_file(file_item))
    print(f"Successfully!")


if __name__ == "__main__":
    welcome = ("Hi, my name is Roman, this program is for extracting rar archive files \n"
               f"(The GNU General Public License v3.0) Mamchiy Roman https://github.com/RomanPM85")
    print(welcome)
    find = input(f"Введите шаблон поиска файла(ов) для получения хэша.\n"
                 f"Если ввести: *.pdf соответствует всем файлам .pdf в папке. \n"
                 f"Если ввести: file*.pdf, соответствует всем файлам file1.pdf, file255.pdf, file2154.pdf в папке.\n"
                 f" * в шаблоне означает любое и неограниченое количество символов. \n"
                 f" ? в шаблоне означает один любой символ. \n"
                 f"остальные возможности шаблонов см.регулярные выражения https://docs.python.org/3/library/re.html\n"
                 f"введите шаблон имени файла\n =>")

    find_files = Path.cwd().glob(find)

    try:
        delete_file("sha256.txt")
        iterating_files_folder(find_files)

    except FileNotFoundError:
        iterating_files_folder(find_files)

    except PermissionError:
        iterating_files_folder(find_files)
