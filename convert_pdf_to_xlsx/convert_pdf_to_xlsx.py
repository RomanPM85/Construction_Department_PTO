import os
import sys
import tabula
import pandas as pd
import sqlite3
import getpass


def extract_tables_from_pdf(pdf_path):
    """Извлекает таблицы из PDF файла."""
    print(f"Извлечение таблиц из {pdf_path}...")
    try:
        # Извлечение всех таблиц из PDF
        tables = tabula.read_pdf(pdf_path, pages='all', multiple_tables=True)
        print(f"Найдено {len(tables)} таблиц в документе.")
        return tables
    except Exception as e:
        print(f"Ошибка при извлечении таблиц: {e}")
        return []


def process_tables(tables):
    """Обрабатывает извлеченные таблицы."""
    if not tables:
        return None

    # Объединяем все таблицы в один DataFrame
    # Предполагаем, что все таблицы имеют одинаковую структуру
    combined_df = pd.concat(tables, ignore_index=True)

    # Очистка данных (удаление пустых строк и столбцов)
    combined_df = combined_df.dropna(how='all')
    combined_df = combined_df.dropna(axis=1, how='all')

    return combined_df


def save_to_excel(dataframe, output_path):
    """Сохраняет DataFrame в Excel файл."""
    try:
        dataframe.to_excel(output_path, index=False, sheet_name='Спецификация')
        print(f"Данные успешно сохранены в {output_path}")
        return True
    except Exception as e:
        print(f"Ошибка при сохранении в Excel: {e}")
        return False


def save_to_sqlite(dataframe, db_path):
    """Сохраняет DataFrame в базу данных SQLite."""
    try:
        # Подключение к базе данных SQLite
        conn = sqlite3.connect(db_path)

        # Создание таблицы, если она не существует
        # Адаптируйте структуру таблицы под ваши данные
        create_table_query = """
        CREATE TABLE IF NOT EXISTS specifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            position TEXT,
            code TEXT,
            name TEXT,
            unit TEXT,
            quantity REAL,
            notes TEXT
        )
        """
        conn.execute(create_table_query)

        # Сохранение DataFrame в SQLite
        # Метод to_sql заменит таблицу, если она уже существует
        dataframe.to_sql('specifications', conn, if_exists='replace', index=False)

        conn.commit()
        print(f"Данные успешно сохранены в базу данных SQLite: {db_path}")
        return True
    except Exception as e:
        print(f"Ошибка при работе с SQLite: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()
            print("Соединение с SQLite закрыто")


def main():
    print("=== Программа для извлечения спецификаций из PDF документов ===")

    # Запрос пути к PDF файлу
    pdf_path = input("Введите путь к PDF файлу: ")

    if not os.path.exists(pdf_path):
        print(f"Файл {pdf_path} не найден!")
        return

    # Извлечение и обработка таблиц
    tables = extract_tables_from_pdf(pdf_path)
    dataframe = process_tables(tables)

    if dataframe is None:
        print("Не удалось извлечь таблицы из документа.")
        return

    # Показать предварительный просмотр данных
    print("\nПредварительный просмотр извлеченных данных:")
    print(dataframe.head())

    # Сохранение в Excel
    save_excel = input("\nСохранить данные в Excel? (да/нет): ").lower()
    if save_excel == 'да':
        output_path = input("Введите путь для сохранения Excel файла: ")
        save_to_excel(dataframe, output_path)

    # Сохранение в SQLite
    save_sqlite = input("\nСохранить данные в SQLite? (да/нет): ").lower()
    if save_sqlite == 'да':
        db_path = input("Введите путь для сохранения базы данных SQLite (например, specifications.db): ")
        save_to_sqlite(dataframe, db_path)

    print("\nОбработка завершена!")


if __name__ == "__main__":
    main()
