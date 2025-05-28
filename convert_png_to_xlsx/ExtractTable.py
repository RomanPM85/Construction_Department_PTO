import layoutparser as lp
import cv2
import pandas as pd
import sqlite3

# Путь к изображению (в той же папке)
image_path = 'Screenshot.png'

# Загружаем изображение
image = cv2.imread(image_path)

# Загружаем модель PaddleDetection для распознавания layout
model = lp.PaddleDetectionLayoutModel('ch_ppocr_layout_mobile_v2')

# Детектируем layout
layout = model.detect(image)

# Функция для распознавания текста в области таблицы
def extract_table_text(image, bbox):
    x1, y1, x2, y2 = map(int, bbox)
    table_crop = image[y1:y2, x1:x2]

    import easyocr
    reader = easyocr.Reader(['en'])  # Можно добавить нужные языки
    result = reader.readtext(table_crop)

    # Группируем текст по строкам
    lines = []
    current_y = -1
    line_text = []
    for (bbox, text, prob) in result:
        y = (bbox[0][1] + bbox[2][1]) / 2
        if current_y == -1 or abs(y - current_y) < 10:
            line_text.append(text)
            current_y = y
        else:
            lines.append(" ".join(line_text))
            line_text = [text]
            current_y = y
    if line_text:
        lines.append(" ".join(line_text))
    return lines

# Собираем все таблицы
all_tables = []

for element in layout:
    if element.type == 'Table':
        bbox = element.coordinates
        table_lines = extract_table_text(image, bbox)
        all_tables.append(table_lines)

# Преобразуем таблицы в DataFrame
dfs = []
for table in all_tables:
    rows = [row.split() for row in table]
    df = pd.DataFrame(rows)
    dfs.append(df)

# Сохраняем таблицы в CSV, XLSX и SQLite

# CSV
for i, df in enumerate(dfs):
    csv_filename = f'table_{i+1}.csv'
    df.to_csv(csv_filename, index=False, header=False)
    print(f"Сохранено {csv_filename}")

# XLSX
with pd.ExcelWriter('tables.xlsx') as writer:
    for i, df in enumerate(dfs):
        df.to_excel(writer, sheet_name=f'Table_{i+1}', index=False, header=False)
print("Сохранено tables.xlsx")

# SQLite
conn = sqlite3.connect('tables.db')
for i, df in enumerate(dfs):
    table_name = f'table_{i+1}'
    df.to_sql(table_name, conn, if_exists='replace', index=False)
print("Сохранено tables.db")
conn.close()
