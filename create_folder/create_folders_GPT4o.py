from pathlib import Path
import sqlite3
import openpyxl

# Определяем структуру папок
folder_structure = {
    "ИРД": {
        "ТУ": {
            "Водоснабжение_и_водоотведение": {},
            "Электроснабжение": {},
            "Газоснабжение": {},
            "Сети_связи": {},
            "Ливневые_стоки": {},
            "Другие_ТУ": {}
        },
        "Собственность": {}
    }
}

# Функция для создания папок
def create_folders(base_path, structure):
    paths = []
    for folder, subfolders in structure.items():
        folder_path = base_path / folder
        folder_path.mkdir(parents=True, exist_ok=True)
        paths.append(str(folder_path))
        if isinstance(subfolders, dict):
            paths.extend(create_folders(folder_path, subfolders))
    return paths

# Сохранение путей в SQLite
def save_to_sqlite(db_path, paths):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS folders (id INTEGER PRIMARY KEY, path TEXT)")
    cursor.executemany("INSERT INTO folders (path) VALUES (?)", [(path,) for path in paths])
    conn.commit()
    conn.close()

# Сохранение путей в Excel
def save_to_excel(file_path, paths):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Paths"
    ws.append(["Path"])
    for path in paths:
        ws.append([path])
    wb.save(file_path)

# Основная часть скрипта
def main():
    base_path = Path.cwd()  # Текущая директория
    db_path = base_path / "folders.db"  # Путь к базе данных SQLite
    excel_path = base_path / "folders.xlsx"  # Путь к файлу Excel

    # Создаём папки и собираем пути
    paths = create_folders(base_path, folder_structure)

    # Сохраняем пути в SQLite
    save_to_sqlite(db_path, paths)

    # Сохраняем пути в Excel
    save_to_excel(excel_path, paths)

    print(f"Структура папок создана в {base_path}")
    print(f"Пути сохранены в {db_path} и {excel_path}")

if __name__ == "__main__":
    main()
