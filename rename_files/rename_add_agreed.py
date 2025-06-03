from pathlib import Path

def add_suffix_to_latest_file(root_dir: Path, suffix="_agreed"):
    for folder in root_dir.rglob('*'):
        if folder.is_dir():
            files = [f for f in folder.iterdir() if f.is_file()]
            if not files:
                continue

            # Если в папке есть файл с суффиксом, пропускаем всю папку
            if any(suffix in f.stem for f in files):
                print(f"Пропущена папка (найден файл с суффиксом): {folder}")
                continue

            # Ищем последний изменённый файл
            latest_file = max(files, key=lambda f: f.stat().st_mtime)

            new_name = latest_file.with_name(latest_file.stem + suffix + latest_file.suffix)

            latest_file.rename(new_name)
            print(f"Переименован: {latest_file} -> {new_name}")

if __name__ == "__main__":
    current_dir = Path.cwd()
    add_suffix_to_latest_file(current_dir)
