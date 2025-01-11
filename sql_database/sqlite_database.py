# -*- encoding: utf-8 -*-

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


if __name__ == "__main__":
    status_2 = 0
    id_2 = 42
    recipients_2 = 'recipients_2@company.ru'
    result_date_2 = date.today().strftime("%Y-%m-%d")
    query_2 = ("SELECT id, recipients, task_name, date_message, result_date FROM message_database "
             "WHERE status = ? "
             "AND recipients = ? "
             "AND id = ? "
             "AND result_date > ?")

    get_list_2 = filter_selected_query(query_2, status_2, recipients_2, id_2, result_date_2)

    for i in get_list_2:
        print(i)
