import zipfile

import patoolib
import time
from pathlib import Path


def extract_archive_rar():
    """ Function for extracting files from rar archives in the current folder """
    path_archives = Path.cwd().rglob('*.rar')
    path_extract_archive = Path.cwd()
    for archive in path_archives:
        patoolib.extract_archive(str(archive), outdir=str(path_extract_archive))


def extract_archive_zip():
    """ Function for extracting files from zip archives in the current folder """
    path_archives = Path.cwd().rglob('*.zip')
    path_extract_archive = Path.cwd()
    for archive in path_archives:
        with zipfile.ZipFile(archive, 'r') as zip_file:
            zip_file.extractall(path_extract_archive)


if __name__ == "__main__":
    program_start_time = time.time()
    welcome = ("Hi, my name is Roman, this program is for extracting rar archive files \n"
               f"(The GNU General Public License v3.0) Mamchiy Roman https://github.com/RomanPM85")

    print(welcome)
    start_script = input(f"Enter the program command number=>.\n"
                         f"If 1, all archives rar in the current folder will be unpacked. \n"
                         f"If 2, all archives zip in the current folder will be unpacked. \n"
                         f"==>"
                         )

    if start_script == '1':
        extract_archive_rar()
    elif start_script == '2':
        extract_archive_zip()
    else:
        print(f"the code is not entered")
print("--- %s seconds ---" % (time.time() - program_start_time))
