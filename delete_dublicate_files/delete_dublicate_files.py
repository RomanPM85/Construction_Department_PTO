import pandas as pd
from pathlib import Path
from openpyxl import load_workbook
from openpyxl.styles import PatternFill
from openpyxl.utils import get_column_letter


def process_duplicates(file_path):
    # Загружаем файл Excel
    xlsx_path = Path(file_path)
    if not xlsx_path.is_file():
        print(f"Файл {xlsx_path} не найден.")
        return

    # Открываем рабочую книгу и выбираем листы
    wb = load_workbook(xlsx_path)
    ws_duplicates = wb['Duplicate_files']  # Рабочий лист 'Duplicate_files'
    ws_delete = wb['Delete']  # Рабочий лист 'Delete'

    # Читаем данные в DataFrame
    df = pd.read_excel(xlsx_path, sheet_name='Duplicate_files', header=0)

    # Получаем все столбцы, начиная с "B" (то есть "Duplicate 1", "Duplicate 2" и т.д.)
    duplicate_columns = [col for col in df.columns if 'Duplicate' in col]

    # Цвет для заливки - голубой
    blue_fill = PatternFill(start_color="ADD8E6", end_color="ADD8E6", fill_type="solid")

    # Список для хранения путей, которые нужно скопировать в лист Delete
    paths_to_delete = []

    # Перебираем строки
    for row_idx, row in df.iterrows():
        # Получаем все пути в текущей строке (не NaN значения)
        paths = [row[col] for col in duplicate_columns if pd.notna(row[col])]

        # Пропускаем, если дубликат только один
        if len(paths) <= 1:
            continue

        # Проверяем наличие пути с текстом "O:\tcsm_pro\%TEMP\"
        temp_paths = []
        for i, path_str in enumerate(paths):
            path = Path(str(path_str))  # Преобразуем путь в объект Path
            if "O:\\tcsm_pro\\%TEMP\\" in str(path):
                temp_paths.append(i)

        # Если есть пути с %TEMP%, выделяем все, кроме последнего
        if temp_paths:
            # Сортируем индексы по возрастанию
            temp_paths.sort()

            # Выделяем все пути с %TEMP%, кроме последнего, и добавляем их в список для копирования
            for i in temp_paths[:-1]:
                col_name = duplicate_columns[i]
                col_idx = df.columns.get_loc(col_name) + 1  # +1 для соответствия с openpyxl (начинается с 1)
                col_letter = get_column_letter(col_idx)
                cell = ws_duplicates[f"{col_letter}{row_idx + 2}"]  # +2 для учета заголовка и 0-индексации pandas
                cell.fill = blue_fill

                # Добавляем путь в список для копирования
                paths_to_delete.append(paths[i])

    # Очищаем лист "Delete" перед копированием данных
    # Удаляем все строки кроме заголовка (если есть)
    for row in range(ws_delete.max_row, 1, -1):
        ws_delete.delete_rows(row)

    # Копируем пути в лист "Delete" в столбец A
    for idx, path in enumerate(paths_to_delete):
        ws_delete[f"A{idx + 2}"] = path  # Начинаем с 2-й строки (A2)

    # Сохраняем изменения в файл
    wb.save(xlsx_path)
    print(f"Обработка завершена. Файл сохранен: {xlsx_path}")
    print(f"Скопировано {len(paths_to_delete)} путей в лист 'Delete'.")


if __name__ == "__main__":
    process_duplicates("duplicates_files_report.xlsx")
