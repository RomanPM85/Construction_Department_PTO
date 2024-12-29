import datetime
import hashlib
import time
import webbrowser
from pathlib import Path

import openpyxl
from openpyxl import load_workbook, Workbook
from openpyxl.utils.cell import get_column_letter
from openpyxl.styles import PatternFill, Alignment, Font, Border, Side
from openpyxl.worksheet.filters import AutoFilter


def get_filenames_recursive_pathlib(directory):
    """Recursively gets all filenames using pathlib."""
    try:
        path = Path(directory)
        return [x for x in path.rglob('*') if x.is_file()]  # Convert Path objects to strings.
        # return [str(x) for x in path.rglob('*') if x.is_file()]  # Convert Path objects to strings.
    except FileNotFoundError:
        print(f"Error: Directory '{directory}' not found.")
        return []
    except OSError as e:
        print(f"An error occurred: {e}")
        return []


def returns_hash_file(file_path):
    """ a function that returns a hash256 file """
    write_date = datetime.datetime.now()
    path_loc = Path(file_path)
    local_paths = path_loc.relative_to(Path.cwd())

    sha256_hash = hashlib.new('sha256')

    with open(file_path, 'rb') as f:
        while True:
            data = f.read(1024)
            if not data:
                break
            sha256_hash.update(data)
        # return f'SHA-256,{sha256_hash.hexdigest()},{file_path.name},{file_path} \n'
        return str(write_date), file_path.name, sha256_hash.hexdigest(), str(local_paths)


def writes_text_file(self):
    """ the function writes data to a file """
    with open("sha256.txt", 'a+', encoding='utf-8') as f:
        f.write(self)


def delete_file(self):
    """ a function that deletes all files """
    try:
        Path.unlink(self)
        return self
    except FileNotFoundError:
        pass


def add_hyperlinks(xlsx_filepath, sheet_name="Sheet", column_index=4):
    """Добавляет гиперссылки в XLSX файл.

    Args:
        xlsx_filepath: Путь к XLSX файлу.
        sheet_name: Имя листа, в котором нужно создавать гиперссылки (по умолчанию "Sheet").
        column_index: Индекс столбца, содержащего пути к файлам (по умолчанию 1 - столбец A).
    """

    try:
        workbook = load_workbook(xlsx_filepath)
        sheet = workbook[sheet_name]

        for iter_row in sheet.iter_rows(min_row=2):
            cell = iter_row[column_index - 1]  # Индекс начинается с 0
            if cell.value:  # Проверяем, есть ли значение в ячейке
                try:
                    #  Создаем гиперссылку.  Если путь некорректный - возникает исключение
                    cell.hyperlink = cell.value
                    cell.style = "Hyperlink"  # Применяем стиль гиперссылки
                    font = Font(underline='single', color='0000FF')  # Цвет и подчеркивание
                    cell.font = font
                    cell.alignment = Alignment(horizontal='left', wrap_text=True)  # Выравнивание
                except Exception as e:
                    print(f"Ошибка при создании гиперссылки для ячейки {cell.coordinate}: {e}")

        workbook.save(xlsx_filepath)  # Сохраняем изменения
        print(f"Гиперссылки успешно добавлены в файл {xlsx_filepath}")

    except FileNotFoundError:
        print(f"Файл {xlsx_filepath} не найден.")
    except Exception as e:
        print(f"Произошла ошибка: {e}")


def stops_the_program_to_write_data(sleep_duration):
    # sleep_duration = 5
    print(f"Даем время программе для записи данных в файл {sleep_duration} сек.")
    for i in range(sleep_duration, 0, -1):
        print(i)
        time.sleep(1)
    print("Программа проснулась!")


def set_auto_column_width(filepath, sheet_name="Sheet"):
    """Автоматически устанавливает ширину столбцов в файле Excel."""
    try:
        workbook = load_workbook(filepath)
        sheet = workbook[sheet_name]
        for col in sheet.columns:
            max_length = 0
            column = col[0].column_letter  # Буква столбца
            for cell in col:
                try:  # Обработка возможных ошибок при получении значения ячейки
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))

                except:
                    pass
            adjusted_width = (max_length + 2) * 1.05  # Добавляем 2 символа запаса и коэф-т для ширины
            sheet.column_dimensions[column].width = adjusted_width
        workbook.save(filepath)
    except FileNotFoundError:
        print(f"Файл {filepath} не найден.")
    except Exception as e:
        print(f"Ошибка: {e}")


def add_header_to_excel(filepath, header_row):
    """Добавляет строку заголовков в существующий файл Excel.

    Args:
        filepath: Путь к существующему файлу Excel.
        header_row: Список значений для строки заголовков.
    """
    try:
        workbook = load_workbook(filepath)
        sheet = workbook.active
        sheet.insert_rows(1, amount=1)  # Вставляем 1 строку перед первой строкой
        # sheet.append(header_row)
        # sheet[1] = header_row    # Записываем заголовки
        for i, value in enumerate(header_row):
            sheet.cell(row=1, column=i + 1, value=value)
        sheet.auto_filter.ref = sheet.dimensions
        workbook.save(filepath)
        print(f"Заголовки добавлены к файлу {filepath}.")
    except FileNotFoundError:
        print(f"Файл {filepath} не найден.")
    except Exception as e:
        print(f"Ошибка: {e}")


def format_first_row(filepath):
    """
    Форматирует первую строку листа: закрашивает, центрирует текст, делает жирным.
    """
    try:
        workbook = load_workbook(filepath)
        sheet = workbook.active

        """ Получаем количество столбцов в первой строке.  Если лист пустой, 
        это может вызвать ошибку, так что добавим обработку
        """
        try:
            num_cols = len(sheet[1])
        except IndexError:
            print("Лист пустой, форматирование невозможно")
            return

        # Стиль заливки
        fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")  # Желтый цвет

        # Стиль выравнивания
        alignment = Alignment(horizontal="center", vertical="center")

        # Стиль шрифта
        font = Font(bold=True)

        #  Применение стилей к первой строке
        for cell in sheet[1]:
            cell.fill = fill
            cell.alignment = alignment
            cell.font = font

        workbook.save(filepath)
        print(f"Первая строка файла {filepath} отформатирована.")

    except FileNotFoundError:
        print(f"Файл {filepath} не найден.")
    except Exception as e:
        print(f"Ошибка: {e}")


def add_border_to_data_cells(filepath):
    """
    Добавляет границу ко всем ячейкам с данными в файле Excel.

    Args:
        filepath: Путь к входному файлу Excel (.xlsx).
    """
    try:
        workbook = load_workbook(filepath)
        sheet = workbook.active  # Или укажите имя листа, если нужно

        # thin_border = Border(all=Side(style="thin"))
        thin_border = Border(left=Side(style='thin'), right=Side(style='thin'),
                             top=Side(style='thin'), bottom=Side(style='thin'))

        for row in sheet.iter_rows():
            for cell in row:
                if cell.value is not None:  # Проверяем, есть ли данные в ячейке
                    cell.border = thin_border

        workbook.save(filepath)
        print(f"Границы добавлены в файл: {filepath}")

    except FileNotFoundError:
        print(f"Файл не найден: {filepath}")
    except Exception as e:
        print(f"Произошла ошибка: {e}")


if __name__ == "__main__":
    welcome = ("Hi, my name is Roman, this program is designed to get a hash of files written to an xlsx file \n"
               f"(The GNU General Public License v3.0) Mamchiy Roman https://github.com/RomanPM85")
    print(welcome)
    directory_path = Path.cwd()
    all_files = get_filenames_recursive_pathlib(directory_path)
    # delete_file("sha256.txt")
    wb = Workbook()
    ws = wb.active

    for file in all_files:
        rows = []
        sha256_file = returns_hash_file(file)
        obj_fun = list(sha256_file)
        rows.append(obj_fun)
        for row in rows:
            ws.append(row)

        # sha256_file = returns_hash_file(file)
        # writes_text_file(str(sha256_file))
        print(f"Successfully! {file.name}")
    wb.save('Реестр_папки_'+str(directory_path.name)+'.xlsx')

    # stops_the_program_to_write_data(1)

    xlsx_file = 'Реестр_папки_' + str(directory_path.name)+'.xlsx'  # Замените на ваш файл

    header = ['date', 'file_name', 'sha256', 'path_file']
    add_header_to_excel(xlsx_file, header)

    add_hyperlinks(xlsx_file)

    format_first_row(xlsx_file)

    set_auto_column_width(xlsx_file)

    add_border_to_data_cells(xlsx_file)
    print(openpyxl.__version__)

    url = f'https://github.com/RomanPM85/Construction_Department_PTO/'
    webbrowser.open_new(url)
