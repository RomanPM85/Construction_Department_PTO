import hashlib
from pathlib import Path


def get_filenames_recursive_pathlib(directory):
    """Recursively gets all filenames using pathlib."""
    try:
        path = Path(directory)
        return [x for x in path.rglob('*') if x.is_file()]  # Convert Path objects to strings.
        # return [str(x) for x in path.rglob('*') if x.is_file()]  # Convert Path objects to strings.
    except FileNotFoundError:
        print(f"Error: Directory '{directory}' not found.")
        return []
    except OSError as e:
        print(f"An error occurred: {e}")
        return []


def returns_hash_file(file_path):
    """ a function that returns a hash256 file """

    sha256_hash = hashlib.new('sha256')

    with open(file_path, 'rb') as f:
        while True:
            data = f.read(1024)
            if not data:
                break
            sha256_hash.update(data)
        return f'SHA-256,{sha256_hash.hexdigest()},{file_path.name},{file_path} \n'


def writes_text_file(self):
    """ the function writes data to a file """
    with open("sha256.txt", 'a+', encoding='utf-8') as f:
        f.write(self)


def delete_file(self):
    """ a function that deletes all files """
    Path.unlink(self)
    return self


if __name__ == "__main__":
    welcome = ("Hi, my name is Roman, this program is for extracting rar archive files \n"
               f"(The GNU General Public License v3.0) Mamchiy Roman https://github.com/RomanPM85")
    print(welcome)
    directory_path = Path.cwd()
    all_files = get_filenames_recursive_pathlib(directory_path)
    delete_file("sha256.txt")
    for file in all_files:
        sha256_file = returns_hash_file(file)
        writes_text_file(str(sha256_file))
        print(f"Successfully! {file.name}")
