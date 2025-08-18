from pathlib import Path
import win32com.client as win32

def convert_xlsx_to_pdf(input_folder: Path, output_folder: Path):
    output_folder.mkdir(parents=True, exist_ok=True)  # Создаем папку, если нет

    excel = win32.gencache.EnsureDispatch('Excel.Application')
    excel.Visible = False

    for xlsx_file in input_folder.glob('*.xlsx'):
        print(f'Обрабатываю файл: {xlsx_file.name}')
        wb = excel.Workbooks.Open(str(xlsx_file.resolve()))
        ws = wb.ActiveSheet

        # Область печати должна быть уже задана в файле Excel

        pdf_file = output_folder / xlsx_file.with_suffix('.pdf').name
        wb.ExportAsFixedFormat(0, str(pdf_file.resolve()))

        wb.Close(False)

    excel.Quit()
    print('Готово!')

if __name__ == "__main__":
    # Путь к папке с файлами xlsx (относительно места запуска скрипта)
    input_folder = Path.cwd() / 'output_files'

    # Путь к папке для сохранения pdf (относительно места запуска скрипта)
    output_folder = Path.cwd() / 'output_files_pdf'

    convert_xlsx_to_pdf(input_folder, output_folder)
