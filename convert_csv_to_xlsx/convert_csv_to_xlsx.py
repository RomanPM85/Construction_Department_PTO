import pandas as pd

def csv_to_xlsx(csv_file, xlsx_file):
    # Читаем CSV
    df = pd.read_csv(csv_file)
    # Сохраняем в Excel
    df.to_excel(xlsx_file, index=False)
    print(f"Файл сохранён: {xlsx_file}")

# Пример использования:
csv_file = "table.csv"   # путь к вашему CSV
xlsx_file = "table.xlsx" # желаемое имя Excel файла

csv_to_xlsx(csv_file, xlsx_file)
