import pandas as pd
from pathlib import Path
import os
import sys
import argparse
import ctypes


def is_admin():
    """
    Проверяет, запущен ли скрипт с правами администратора

    :return: True если скрипт запущен с правами администратора, иначе False
    """
    try:
        if os.name == 'nt':  # Windows
            return ctypes.windll.shell32.IsUserAnAdmin()
        else:  # Unix/Linux/Mac
            # Для Unix-подобных систем проверяем UID пользователя
            return os.geteuid() == 0
    except:
        return False


def run_as_admin():
    """
    Перезапускает скрипт с правами администратора
    """
    if os.name == 'nt':  # Windows
        script = sys.argv[0]
        params = ' '.join(sys.argv[1:])

        # Формируем команду для запуска с правами администратора
        cmd = f'powershell Start-Process -FilePath "python" -ArgumentList "{script} {params}" -Verb RunAs'

        # Запускаем команду
        os.system(cmd)
    else:
        # Для Unix-подобных систем используем sudo
        script = sys.argv[0]
        params = ' '.join(sys.argv[1:])
        os.system(f'sudo python {script} {params}')


def create_excel_template(excel_path):
    """
    Создает шаблон Excel-файла с необходимыми листами и столбцами

    :param excel_path: путь для сохранения Excel-файла
    """
    try:
        # Создаем DataFrame с нужными столбцами
        df = pd.DataFrame(columns=['FileName', 'FilePath', 'OriginFilePath'])

        # Создаем пример данных
        example_data = {
            'FileName': ['example.txt', 'document.pdf'],
            'FilePath': ['C:/Target/Path1', 'C:/Target/Path2'],
            'OriginFilePath': ['C:/Source/Path1', 'C:/Source/Path2']
        }

        # Добавляем примеры данных
        example_df = pd.DataFrame(example_data)
        df = pd.concat([df, example_df], ignore_index=True)

        # Сохраняем в Excel
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='data', index=False)

        print(f"Создан шаблон Excel-файла: {excel_path}")
        print("Заполните его данными и запустите скрипт снова.")

    except Exception as e:
        print(f"Ошибка при создании шаблона Excel: {e}")


def create_file_links(excel_path):
    """
    Создает символические ссылки на файлы из указанных папок в целевые папки
    на основе данных из Excel-таблицы.

    :param excel_path: путь к Excel-файлу с данными
    """
    # Проверяем существование Excel-файла
    excel_file = Path(excel_path)
    if not excel_file.exists():
        print(f"Файл {excel_path} не найден. Создаем шаблон...")
        create_excel_template(excel_path)
        return

    try:
        # Загружаем данные из Excel
        print(f"Загрузка данных из файла: {excel_path}")
        df = pd.read_excel(excel_path, sheet_name='data')

        # Проверяем наличие необходимых столбцов
        required_columns = ['FileName', 'FilePath', 'OriginFilePath']
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            print(f"Ошибка: В Excel-файле отсутствуют столбцы: {', '.join(missing_columns)}")
            print("Создаем новый шаблон с правильной структурой...")
            create_excel_template(excel_path + ".new.xlsx")
            return

        # Счетчики для статистики
        success_count = 0
        error_count = 0

        # Обрабатываем каждую строку в таблице
        for index, row in df.iterrows():
            file_name = row['FileName']
            file_path = row['FilePath']
            origin_file_path = row['OriginFilePath']

            # Проверяем, что значения не пустые
            if pd.isna(file_name) or pd.isna(file_path) or pd.isna(origin_file_path):
                print(f"Пропуск строки {index + 2}: пустое значение в одном из обязательных полей")
                error_count += 1
                continue

            # Преобразуем пути в объекты Path
            source_file = Path(origin_file_path) / file_name
            if not source_file.is_file():
                # Проверяем, возможно путь уже включает имя файла
                source_file = Path(origin_file_path)
                if not source_file.is_file():
                    print(f"Ошибка: Исходный файл не существует: {source_file}")
                    error_count += 1
                    continue
                # Если путь уже включает имя файла, обновляем file_name
                file_name = source_file.name

            target_dir = Path(file_path)
            target_link = target_dir / file_name

            try:
                # Проверяем существование целевой директории, создаем при необходимости
                if not target_dir.exists():
                    print(f"Создание директории: {target_dir}")
                    target_dir.mkdir(parents=True, exist_ok=True)

                # Проверяем, существует ли уже ссылка или файл с таким именем
                if target_link.exists() or target_link.is_symlink():
                    print(f"Предупреждение: Ссылка или файл уже существует: {target_link}")
                    # Удаляем существующую ссылку
                    target_link.unlink()

                # Создаем символическую ссылку
                target_link.symlink_to(source_file)
                print(f"Создана ссылка: {source_file} -> {target_link}")
                success_count += 1

            except PermissionError:
                print(f"Ошибка доступа: Недостаточно прав для создания ссылки {target_link}")
                error_count += 1
            except OSError as e:
                print(f"Ошибка ОС: {e} при создании ссылки {target_link}")
                error_count += 1

        # Выводим итоговую статистику
        print("\nСтатистика:")
        print(f"Успешно создано ссылок: {success_count}")
        print(f"Ошибок: {error_count}")

    except FileNotFoundError:
        print(f"Ошибка: Файл не найден: {excel_path}")
    except pd.errors.EmptyDataError:
        print(f"Ошибка: Файл {excel_path} не содержит данных")
    except Exception as e:
        print(f"Непредвиденная ошибка: {e}")
        import traceback
        traceback.print_exc()


def main():
    # Проверяем права администратора и перезапускаем скрипт при необходимости
    if not is_admin():
        print("Для создания символических ссылок требуются права администратора.")
        print("Запрашиваем права администратора...")
        run_as_admin()
        sys.exit(0)

    # Создаем парсер аргументов командной строки
    parser = argparse.ArgumentParser(description='Создание символических ссылок на основе данных из Excel')
    parser.add_argument('excel_file', nargs='?', default='links.xlsx',
                        help='Путь к Excel-файлу с данными (по умолчанию: links.xlsx)')

    # Разбираем аргументы
    args = parser.parse_args()

    # Запускаем основную функцию
    create_file_links(args.excel_file)


if __name__ == "__main__":
    main()
