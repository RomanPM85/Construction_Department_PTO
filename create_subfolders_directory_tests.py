from pathlib import Path

"""
Скрипт проверяет все подпапки в текущей директории.
Если в подпапке нет папки "tests", создает ее.
Если папка "tests" уже существует, пропускает эту подпапку.
"""

def create_tests_folder():
    # Получаем текущую директорию
    current_dir = Path('.')

    # Перебираем все объекты в текущей директории
    for item in current_dir.iterdir():
        # Проверяем, что это директория (папка) и не начинается с точки
        if item.is_dir() and not item.name.startswith('.'):
            # Проверяем, есть ли подпапка "tests"
            tests_dir = item / "tests"
            if not tests_dir.exists():
                # Если нет - создаем
                tests_dir.mkdir()
                print(f"Создана папка 'tests' в {item}")
            else:
                # Если есть - пропускаем
                print(f"Папка 'tests' уже существует в {item}, пропускаем")

if __name__ == "__main__":
    create_tests_folder()
