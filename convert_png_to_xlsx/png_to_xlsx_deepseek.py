import cv2
import pytesseract
import pandas as pd
from pytesseract import Output

# Настройки (укажите свой путь к Tesseract)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Windows


# Для Linux/Mac: sudo apt install tesseract-ocr / brew install tesseract

def image_to_excel(input_image, output_excel):
    # 1. Загрузка и предобработка изображения
    img = cv2.imread(input_image)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    # 2. Распознавание структуры таблицы
    custom_config = r"[--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ.,$-%/\]"
    data = pytesseract.image_to_data(thresh, config=custom_config, output_type=Output.DICT)

    # 3. Обработка и структурирование данных
    df = pd.DataFrame(data)
    df = df[df['conf'] > 60]  # Фильтр по уверенности распознавания
    df = df.sort_values(by=['page_num', 'block_num', 'par_num', 'line_num', 'word_num'])

    # 4. Создание структуры таблицы
    table_data = []
    current_row = []
    prev_y = 0

    for index, row in df.iterrows():
        if abs(row['top'] - prev_y) > 10:  # Определение новой строки
            if current_row:
                table_data.append(current_row)
            current_row = []
        current_row.append(row['text'])
        prev_y = row['top']

    if current_row:
        table_data.append(current_row)

    # 5. Экспорт в Excel
    max_cols = max(len(row) for row in table_data)
    columns = [f'Column_{i + 1}' for i in range(max_cols)]

    final_df = pd.DataFrame(table_data, columns=columns)
    final_df.to_excel(output_excel, index=False)
    print(f'Файл успешно сохранен: {output_excel}')


# Использование
image_to_excel('input_table2.png', 'output_table.xlsx')
