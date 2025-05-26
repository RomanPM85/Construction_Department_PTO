from PIL import Image
import pytesseract
import pandas as pd
from pathlib import Path

def extract_table_from_image(image_path):
    """ Функция извлекает текст из изображения """
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img)
    return text.strip().splitlines()

def convert_text_to_dataframe(lines):
    """ Преобразует извлечённые строки в DataFrame """
    rows = []
    for line in lines:
        row = line.split()
        rows.append(row)
    df = pd.DataFrame(rows)
    return df

def save_to_excel(df, output_file):
    """ Сохраняет DataFrame в Excel-файл """
    df.to_excel(output_file, index=False, header=None)

if __name__ == "__main__":
    #image_path = input("Введите путь к изображению (PNG): ")
    #outpath = Path.cwd()

    image_path = Path.cwd() / "input_table2.PNG"
    print(image_path)
    #excel_output = input("Введите имя выходного Excel-файла (.xlsx): ")
    excel_output = Path.cwd() / "input_table2.xlsx"
    print(excel_output)
    extracted_lines = extract_table_from_image(image_path)
    dataframe = convert_text_to_dataframe(extracted_lines)
    save_to_excel(dataframe, excel_output)

    print(f"Таблица успешно сохранена в {excel_output}.")
