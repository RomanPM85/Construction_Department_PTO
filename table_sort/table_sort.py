import json
import pandas as pd

# Загрузка данных из файла JSON с использованием UTF-8 кодировки
with open('var.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Создание DataFrame из данных
df = pd.DataFrame(data)

# Транспонирование DataFrame для вертикального расположения данных
df = df.T
df.index.name = 'Параметр'
df.columns.name = 'Модель'

# Стилизация таблицы
styler = df.style \
    .set_properties(**{'text-align': 'center', 'padding': '5px'}) \
    .set_table_styles([
        {'selector': 'th', 'props': [('background-color', '#f2f2f2'), ('font-weight', 'bold')]},
        {'selector': 'td', 'props': [('border-right', '1px solid #ddd')]}
    ]) \
    .highlight_max(color='lightgreen', axis=1) \
    .highlight_min(color='lightpink', axis=1)

# Сохранение таблицы в XLSX-файл
styler.to_excel('сравнительная_таблица.xlsx', engine='openpyxl')
print('Сравнительная таблица сохранена в файл "сравнительная_таблица.xlsx"')
