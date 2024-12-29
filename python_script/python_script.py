import subprocess
import os
from pathlib import Path

path_dir_abs = Path.cwd()

path_dirs_local = [
    "folder/folder/folder/folder/",
    "folder/folder/folder/",
    "folder//folder/",
    "folder/"
]


for dir_local in path_dirs_local:
    file = "test.py"
    local_item_dir = path_dir_abs / dir_local
    os.chdir(local_item_dir)
    subprocess.run(['python', file])
