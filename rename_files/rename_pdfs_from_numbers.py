from pathlib import Path

current_dir = Path('.')
pdf_files = sorted(current_dir.glob('*.pdf'))

start_num = 1  # начиная с 0001.pdf

for i, pdf_file in enumerate(pdf_files, start=start_num):
    new_name = f"{i:04d}.pdf"  # формат с ведущими нулями, 4 цифры
    new_path = current_dir / new_name
    # Проверка, чтобы не переименовывать файл в сам себя
    if pdf_file.name != new_name:
        print(f"Переименование: {pdf_file.name} -> {new_name}")
        pdf_file.rename(new_path)
