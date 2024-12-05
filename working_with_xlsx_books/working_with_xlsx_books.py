from openpyxl import load_workbook, Workbook
import os


def merge_xlsx_files(output_filepath, *input_filepaths):
    """Объединяет несколько файлов XLSX в один.

    Args:
        output_filepath: Путь к новому файлу XLSX, в который будут записаны данные.
        *input_filepaths: Список путей к файлам XLSX, которые нужно объединить.
    """

    try:
        workbook = Workbook()
        sheet = workbook.active

        for input_filepath in input_filepaths:
            try:
                input_workbook = load_workbook(input_filepath)
                for sheet_name in input_workbook.sheetnames:
                    input_sheet = input_workbook[sheet_name]
                    # Копируем данные из листа:
                    for row in input_sheet.iter_rows():
                        sheet.append([cell.value for cell in row])
            except FileNotFoundError:
                print(f"Файл {input_filepath} не найден.")
            except Exception as e:
                print(f"Ошибка при обработке файла {input_filepath}: {e}")

        workbook.save(output_filepath)
        print(f"Файлы успешно объединены в {output_filepath}")

    except Exception as e:
        print(f"Произошла общая ошибка: {e}")


if __name__ == "__main__":
    # Пример использования:
    output_file = "merged_file.xlsx"
    input_files = ['file1', 'file2', 'file...']  # Замените на ваши файлы

    # Проверка существования файлов перед запуском
    if all(os.path.exists(file) for file in input_files):
        merge_xlsx_files(output_file, *input_files)
    else:
        print("Один или несколько файлов не найдены.")
