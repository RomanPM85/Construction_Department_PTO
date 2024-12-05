from pathlib import Path


def get_filenames_recursive_pathlib(directory):
    """Recursively gets all filenames using pathlib."""
    try:
        path = Path(directory)
        search_mask = input(f'введите маску для поиска файлов:')
        return [x for x in path.rglob(search_mask) if x.is_file()]  # Convert Path objects to strings.

    except FileNotFoundError:
        print(f"Error: Directory '{directory}' not found.")
        return []
    except OSError as e:
        print(f"An error occurred: {e}")
        return []


if __name__ == "__main__":
    welcome = ("Hi, my name is Roman, \n"
               f"(The GNU General Public License v3.0) Mamchiy Roman https://github.com/RomanPM85")
    print(welcome)
    directory_path = Path.cwd()
    all_files = get_filenames_recursive_pathlib(directory_path)
    for i in all_files:
        print(i)
