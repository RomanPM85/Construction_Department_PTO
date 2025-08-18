from pathlib import Path
import win32com.client as win32

def convert_xlsx_to_pdf(input_folder: Path, output_folder: Path):
    output_folder.mkdir(exist_ok=True)  # Создаем папку, если нет

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
    current_folder = Path.cwd()
    output_folder = current_folder / 'output_files'
    convert_xlsx_to_pdf(current_folder, output_folder)
