import jpg2pdf
from pathlib import Path


def convert_jpg_to_pdf(name_file):
    path = Path.cwd()
    python_files = path.glob('**/*.jp*g')

    with jpg2pdf.create(name_file) as pdf_file:

        for jpeg in python_files:
            # print(jpeg)
            pdf_file.add(jpeg)


if __name__ == "__main__":
    name_create_pdf = input(f"Ведите имя создаваемого файла =>")
    convert_jpg_to_pdf(name_create_pdf + '.pdf')
