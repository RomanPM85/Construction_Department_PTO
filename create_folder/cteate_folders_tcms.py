from pathlib import Path


lines = Path('folders_tcms.txt').read_text(encoding='utf-8').splitlines()

for folder in lines:
    Path(folder).mkdir(parents=True, exist_ok=True)
