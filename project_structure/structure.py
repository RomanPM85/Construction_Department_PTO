from pathlib import Path

def visualize_directory(path: Path, prefix=""):
    lines = []
    try:
        entries = sorted(path.iterdir(), key=lambda p: p.name.lower())
    except PermissionError:
        lines.append(prefix + "└── [Permission Denied]")
        return lines

    count = len(entries)
    for i, entry in enumerate(entries):
        connector = "└── " if i == count - 1 else "├── "
        lines.append(prefix + connector + entry.name)
        if entry.is_dir():
            extension = "    " if i == count - 1 else "│   "
            lines.extend(visualize_directory(entry, prefix + extension))
    return lines

def save_structure_to_file(root_path: Path, output_file: str):
    if not root_path.exists():
        print(f"Путь {root_path} не существует.")
        return

    tree_lines = [str(root_path)]
    tree_lines.extend(visualize_directory(root_path))
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(tree_lines))
    print(f"Структура папки сохранена в файл: {output_file}")

if __name__ == "__main__":
    # Анализируем текущую рабочую директорию
    folder_path = Path.cwd()
    output_txt = "folder_structure.txt"
    save_structure_to_file(folder_path, output_txt)
