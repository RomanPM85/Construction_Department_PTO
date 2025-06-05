import hashlib
from pathlib import Path
import pandas as pd

def sha256sum(file_path: Path) -> str:
    h = hashlib.sha256()
    with file_path.open('rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def find_duplicates(root_folder: Path):
    hash_dict = {}
    for file_path in root_folder.rglob('*'):
        if file_path.is_file():
            try:
                file_hash = sha256sum(file_path)
            except Exception as e:
                print(f"Ошибка при обработке файла {file_path}: {e}")
                continue
            hash_dict.setdefault(file_hash, []).append(str(file_path.resolve()))
    # Оставляем только те хэши, у которых больше одного файла
    return {h: paths for h, paths in hash_dict.items() if len(paths) > 1}

def save_to_excel(duplicates: dict, output_file: Path):
    rows = []
    for files in duplicates.values():
        # Первый файл в первый столбец, остальные — в последующие
        rows.append(files)
    max_len = max(len(r) for r in rows)
    columns = [f'Файл {i+1}' for i in range(max_len)]
    df = pd.DataFrame(rows, columns=columns)
    df.to_excel(output_file, index=False)
    print(f"Результаты сохранены в {output_file}")

if __name__ == "__main__":
    folder_input = input("Введите путь к папке для проверки: ").strip()
    folder_to_check = Path(folder_input)
    output_excel = Path("duplicates.xlsx")

    if not folder_to_check.is_dir():
        print(f"Путь {folder_to_check} не является директорией.")
    else:
        duplicates = find_duplicates(folder_to_check)
        if duplicates:
            save_to_excel(duplicates, output_excel)
        else:
            print("Дубликаты не найдены.")
