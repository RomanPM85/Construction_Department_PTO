from docx2pdf import convert
from pathlib import Path

current_dir = Path.cwd() / 'output_pdf'
current_dir.mkdir(parents=True, exist_ok=True)
paths = sorted(Path('.').glob('*.docx'))
ls = list(map(str, paths))

for i in ls:
    convert(i, current_dir)
