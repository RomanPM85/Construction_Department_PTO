from openpyxl import Workbook

# Создаем новую книгу Excel
wb = Workbook()
ws = wb.active
ws.title = "Документы"

# Заголовки столбцов
headers = [
    "id",
    "Тип документа",
    "Номер документа",
    "Дата документа",
    "Срок действия от",
    "Срок действия до",
    "Наименование продукции",
    "Краткое наименование",
    "Наименование изготовителя",
    "Примечание"
]

# Записываем заголовки в первую строку
ws.append(headers)

# Сохраняем файл
wb.save("documents_template.xlsx")

print("Файл 'documents_template.xlsx' создан.")
