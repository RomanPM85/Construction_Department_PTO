import csv
from openpyxl import Workbook
from pathlib import Path

def convert_csv_to_xlsx(csv_path: Path):
    """
    Конвертирует один CSV-файл в XLSX с тем же именем и в той же папке.
    :param csv_path: Путь к CSV-файлу (Path или str)
    """
    csv_path = Path(csv_path)
    if not csv_path.is_file() or csv_path.suffix.lower() != '.csv':
        print(f"Файл не найден или не CSV: {csv_path}")
        return

    xlsx_path = csv_path.with_suffix('.xlsx')
    wb = Workbook()
    ws = wb.active

    with csv_path.open(encoding='utf-8-sig', newline='') as f:
        reader = csv.reader(f, delimiter=',')
        for row in reader:
            ws.append(row)

    wb.save(xlsx_path)
    print(f"Конвертирован: {csv_path.name} -> {xlsx_path.name}")

def convert_all_csv_to_xlsx_in_cwd():
    """
    Находит все CSV файлы в текущей папке и конвертирует их в XLSX с тем же именем.
    """
    cwd = Path.cwd()
    csv_files = list(cwd.glob('*.csv'))

    if not csv_files:
        print("CSV файлы в текущей папке не найдены.")
        return

    for csv_path in csv_files:
        convert_csv_to_xlsx(csv_path)

if __name__ == "__main__":
    print("Выберите метод конвертации:")
    print("1 - Конвертировать конкретный CSV-файл (укажите путь)")
    print("2 - Конвертировать все CSV-файлы в текущей папке")
    choice = input("Введите 1 или 2: ").strip()

    if choice == '1':
        path_input = input("Введите путь к CSV-файлу: ").strip()
        convert_csv_to_xlsx(path_input)
    elif choice == '2':
        convert_all_csv_to_xlsx_in_cwd()
    else:
        print("Неверный выбор. Запустите программу заново и выберите 1 или 2.")
