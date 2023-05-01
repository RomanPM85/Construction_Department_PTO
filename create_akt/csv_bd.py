import openpyxl
import csv

infile = 'BD_akt.xlsx'
output = 'value_bd.csv'
wb = openpyxl.load_workbook(infile)
sh = wb.active # was .get_active_sheet()
with open(output, 'w', encoding='utf-8', newline="") as file_handle:
    csv_writer = csv.writer(file_handle)
    for row in sh.iter_rows(): # generator; was sh.rows
        csv_writer.writerow([cell.value for cell in row])
