# -*- encoding: utf-8 -*-
import pandas as pd
import sqlite3
from pathlib import Path


path_dir_abs = Path.cwd()
file_path = path_dir_abs /'xlsx_database.xlsx'
sheet_name = 'date'

data = pd.read_excel(file_path, sheet_name=sheet_name)
connection = sqlite3.connect('xlsx_database.sqlite')
cursor = connection.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS medical_center (
id INTEGER PRIMARY KEY, 
task TEXT NOT NULL, 
status INTEGER, 
stage TEXT NOT NULL,
message_date DATE NOT NULL, 
final_date DATE NOT NULL
)''')

data.to_sql('medical_center', connection, if_exists='replace', index=False)


def filter_date() -> list:
    cursor.execute('SELECT task, status, final_date FROM medical_center '
                   'WHERE final_date < ?', ('2024-09-01',))
    final_date = cursor.fetchall()
    return final_date


def get_select() -> list:
    # cursor.execute("SELECT status, final_date FROM medical_center WHERE status=1")
    cursor.execute("SELECT task, final_date FROM medical_center "
                   "WHERE final_date<'2024-09-01' "
                   "AND status=1 "
                   "AND stage='ИРД' "
                   "AND final_date>'2024-07-09'")
    select_all = cursor.fetchall()
    return select_all


get_list_1 = filter_date()
get_list_2 = get_select()
connection.close()


for i in get_list_2:
    print(i)

print(type(get_list_2))
for i in get_list_1:
    print(i)
print(type(get_list_1))

