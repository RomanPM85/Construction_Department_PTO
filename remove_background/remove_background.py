from rembg import remove
from PIL import Image
from pathlib import Path

def remove_bg_with_rembg(input_path: Path, output_path: Path):
    input_img = Image.open(input_path)
    output_img = remove(input_img)
    output_img.save(output_path)
    print(f"Фон удалён и сохранён: {output_path}")

# Пример
remove_bg_with_rembg(Path("input.jpg"), Path("output.png"))
