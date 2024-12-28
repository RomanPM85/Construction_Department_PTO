import subprocess
from pathlib import Path

path_file = Path.cwd() / "dir" / "file.py"

result = subprocess.run(['python', path_file])

