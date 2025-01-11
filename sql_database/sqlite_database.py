# -*- encoding: utf-8 -*-
from collections import defaultdict

import pandas as pd
import sqlite3
from pathlib import Path
from datetime import date

path_dir_abs = Path.cwd()
file_path = path_dir_abs / 'xlsx_database.xlsx'
sheet_name = 'message_database'
data = pd.read_excel(file_path, sheet_name=sheet_name)


connection = sqlite3.connect('xlsx_database.sqlite')
cursor = connection.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS message_database (
id INTEGER PRIMARY KEY AUTOINCREMENT,
task_name TEXT NOT NULL,
stage TEXT NOT NULL,
status INTEGER,
date_message DATE NOT NULL,
recipients TEXT NOT NULL,
copy_recipients TEXT NOT NULL,
result_date DATE NOT NULL
)''')

data.to_sql('message_database', connection, if_exists='replace', index=False)
connection.close()


def filter_selected_query(query, *args) -> list:
    conn = sqlite3.connect('xlsx_database.sqlite')
    cur = conn.cursor()
    cur.execute(query, args)
    select_all = cur.fetchall()
    conn.close()
    return select_all


def list_of_tuples_to_dict(data_value):
    """Преобразует список кортежей в словарь, используя defaultdict."""
    result_dict = defaultdict(list)
    for item in data_value:
        key = item[0]
        value = item[1:]
        result_dict[key].append(value)
    return dict(result_dict)


if __name__ == "__main__":

    status = 0
    recipients = 'recipients_2@company.ru'
    result_date = date.today().strftime("%Y-%m-%d")

    query_2 = ("SELECT id, recipients, task_name, date_message, result_date FROM message_database "
             "WHERE status = ? "
             "AND recipients = ? "
             "AND id = ? "
             "AND result_date > ?")
    id_2 = 42
    get_query_2 = filter_selected_query(query_2, status, recipients, id_2, result_date)

    query_3 = ("SELECT recipients, task_name, date_message, result_date FROM message_database "
             "WHERE status = ? "
             "AND recipients = ? "
             "AND result_date > ?")
    get_query_3 = filter_selected_query(query_3, status, recipients, result_date)

    for i in get_query_2:
        print(i)
    print("_" * 40)
    for i in get_query_3:
        print(i)
    print("_" * 40)

    query_result_date = list_of_tuples_to_dict(get_query_3)
    for key in query_result_date.values():
        item = key
        for i in item:
            print(i)
