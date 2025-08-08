import os
import zipfile
import tarfile

def extract_archive(archive_path, extract_to=None):
    if extract_to is None:
        extract_to = os.path.splitext(archive_path)[0]

    os.makedirs(extract_to, exist_ok=True)
    print(f"Разархивируем {archive_path} в {extract_to}")

    if archive_path.endswith('.zip'):
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
    elif archive_path.endswith(('.tar.gz', '.tgz')):
        with tarfile.open(archive_path, 'r:gz') as tar_ref:
            tar_ref.extractall(extract_to)
    elif archive_path.endswith('.tar'):
        with tarfile.open(archive_path, 'r:') as tar_ref:
            tar_ref.extractall(extract_to)
    else:
        print(f"Неизвестный формат: {archive_path}")
        return

    # Рекурсивно ищем архивы внутри распакованной папки
    for root, _, files in os.walk(extract_to):
        for file in files:
            if file.endswith(('.zip', '.tar.gz', '.tgz', '.tar')):
                inner_archive = os.path.join(root, file)
                extract_archive(inner_archive)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Использование: python extract_recursive.py <архив>")
        sys.exit(1)

    extract_archive(sys.argv[1])
