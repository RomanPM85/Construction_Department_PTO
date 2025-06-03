from pathlib import Path

def add_suffix_to_latest_file(root_dir: Path, suffix="_agreed"):
    for folder in root_dir.rglob('*'):
        if folder.is_dir():
            files = [f for f in folder.iterdir() if f.is_file()]
            if not files:
                continue

            # Находим файл с максимальным временем изменения
            latest_file = max(files, key=lambda f: f.stat().st_mtime)

            # Формируем новое имя с суффиксом перед расширением
            new_name = latest_file.with_name(latest_file.stem + suffix + latest_file.suffix)

            # Переименование
            latest_file.rename(new_name)
            print(f"Переименован: {latest_file} -> {new_name}")

if __name__ == "__main__":
    current_dir = Path.cwd()
    add_suffix_to_latest_file(current_dir)
