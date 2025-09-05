from docx2pdf import convert
from pathlib import Path
import os
import comtypes.client  # Для конвертации .doc в .docx (только Windows)

def doc_to_docx(doc_path):
    word = comtypes.client.CreateObject('Word.Application')
    word.Visible = False
    full_path = str(doc_path.resolve())
    print(f"Открываем файл: {full_path}, существует: {doc_path.exists()}")
    doc = word.Documents.Open(full_path)
    docx_path = str(doc_path.with_suffix('.docx').resolve())
    doc.SaveAs(docx_path, FileFormat=16)  # 16 - формат docx
    doc.Close()
    word.Quit()
    return docx_path



current_dir = Path.cwd() / 'output_pdf'
current_dir.mkdir(parents=True, exist_ok=True)

paths_doc = sorted(Path('.').glob('*.doc'))
paths_docx = sorted(Path('.').glob('*.docx'))

# Конвертация .doc в .docx
docx_files_from_doc = []
for doc_file in paths_doc:
    docx_file = doc_to_docx(doc_file)
    docx_files_from_doc.append(docx_file)

# Все docx файлы для конвертации в PDF
all_docx_files = list(map(str, paths_docx)) + docx_files_from_doc

for docx_file in all_docx_files:
    convert(docx_file, current_dir)
