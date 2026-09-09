import json
import hashlib
import time
from pathlib import Path
from pdf2image import convert_from_path, pdfinfo_from_path

# =========================
# Настройки
# =========================
DPI = 180  # 150-220 обычно оптимально: меньше RAM и быстрее, чем 300+
JPEG_QUALITY = 85
# Если poppler не в PATH, раскомментируйте и укажите путь:
# POPPLER_PATH = Path(r"C:\poppler\Library\bin")
POPLER_PATH = None


# =========================
# Утилиты
# =========================
def safe_stem(pdf_path: Path) -> str:
    """Безопасное имя папки из имени файла."""
    name = pdf_path.stem.strip().replace(" ", "_")
    bad = '<>:"/\\|?*'
    for ch in bad:
        name = name.replace(ch, "_")
    return name


def file_hash_sha256(file_path: Path, chunk_size: int = 1024 * 1024) -> str:
    """SHA256 файла (потоково, без загрузки целиком в память)."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def manifest_path_for(output_dir: Path) -> Path:
    return output_dir / "manifest.json"


def load_manifest(output_dir: Path) -> dict | None:
    mpath = manifest_path_for(output_dir)
    if not mpath.exists():
        return None
    try:
        return json.loads(mpath.read_text(encoding="utf-8"))
    except Exception:
        return None


def save_manifest(output_dir: Path, data: dict) -> None:
    mpath = manifest_path_for(output_dir)
    mpath.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def is_already_converted(pdf_file: Path, output_dir: Path, pages_expected: int | None = None) -> bool:
    """
    Проверка:
    1) manifest существует и совпадает hash+size+mtime;
    2) есть page-*.jpg (и при известном pages_expected их количество совпадает).
    """
    manifest = load_manifest(output_dir)
    if not manifest:
        return False
    try:
        current_stat = pdf_file.stat()
    except FileNotFoundError:
        return False

    old_hash = manifest.get("sha256")
    old_size = manifest.get("size")
    old_mtime = manifest.get("mtime")
    old_pages = manifest.get("pages")

    # Быстрая проверка metadata + hash
    if old_size != current_stat.st_size:
        return False
    if abs(old_mtime - current_stat.st_mtime) > 1e-6:
        return False

    current_hash = file_hash_sha256(pdf_file)
    if current_hash != old_hash:
        return False

    jpg_files = sorted(output_dir.glob("page-*.jpg"))
    if not jpg_files:
        return False
    if pages_expected is not None and len(jpg_files) != pages_expected:
        return False
    if old_pages is not None and len(jpg_files) != old_pages:
        return False
    return True


def convert_pdf_to_jpg_streaming(pdf_file: Path, output_dir: Path, dpi: int = DPI,
                                 jpeg_quality: int = JPEG_QUALITY) -> None:
    """Конвертация PDF -> JPG постранично (одна страница за раз), чтобы избежать MemoryError."""
    output_dir.mkdir(parents=True, exist_ok=True)
    info = pdfinfo_from_path(
        str(pdf_file),
        poppler_path=str(POPLER_PATH) if POPLER_PATH else None
    )
    total_pages = int(info.get("Pages", 0))
    if total_pages <= 0:
        print(f" [ОШИБКА] Не удалось определить страницы: {pdf_file.name}")
        return

    if is_already_converted(pdf_file, output_dir, pages_expected=total_pages):
        print(f"[SKIP] Уже конвертировался: {pdf_file.name}")
        return

    print(f"[START] {pdf_file.name} -> {output_dir} (страниц: {total_pages})")
    for page in range(1, total_pages + 1):
        out_file = output_dir / f"page-{page:04d}.jpg"
        if out_file.exists():
            print(f" [=] Страница {page}/{total_pages} уже есть")
            continue

        images = convert_from_path(
            str(pdf_file),
            dpi=dpi,
            first_page=page,
            last_page=page,
            fmt="jpeg",
            thread_count=1,
            poppler_path=str(POPLER_PATH) if POPLER_PATH else None
        )
        if not images:
            print(f" [!] Не удалось получить страницу {page}")
            continue

        img = images[0]
        img.save(out_file, "JPEG", quality=jpeg_quality, optimize=True)
        img.close()
        del images
        print(f" [+] Страница {page}/{total_pages}: {out_file.name}")

    st = pdf_file.stat()
    manifest = {
        "source_file": str(pdf_file.resolve()),
        "source_name": pdf_file.name,
        "size": st.st_size,
        "mtime": st.st_mtime,
        "sha256": file_hash_sha256(pdf_file),
        "pages": total_pages,
        "dpi": dpi,
        "jpeg_quality": jpeg_quality,
        "converted_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    save_manifest(output_dir, manifest)
    print(f"[DONE] {pdf_file.name}\n")


def find_pdf_files(root: Path) -> list[Path]:
    return sorted([p for p in root.glob("*.pdf") if p.is_file()])


def convert_all_pdfs(root: Path, output_root: Path) -> None:
    pdfs = find_pdf_files(root)
    if not pdfs:
        print("PDF файлы в выбранной папке не найдены.")
        return
    output_root.mkdir(exist_ok=True)
    for pdf in pdfs:
        out_dir = output_root / safe_stem(pdf)
        convert_pdf_to_jpg_streaming(pdf, out_dir)


def convert_single_pdf(root: Path, output_root: Path, filename: str) -> None:
    pdf = (root / filename).resolve()
    if not pdf.exists() or pdf.suffix.lower() != ".pdf":
        print(f"Файл не найден или не PDF: {filename}")
        return
    output_root.mkdir(exist_ok=True)
    out_dir = output_root / safe_stem(pdf)
    convert_pdf_to_jpg_streaming(pdf, out_dir)


def select_working_dir() -> Path:
    """Запрашивает у пользователя папку для поиска PDF-файлов."""
    print("Выберите папку для поиска PDF:")
    print("1 - Текущая папка скрипта")
    print("2 - Указать свой путь к папке")
    choice = input("==> ").strip()
    if choice == "2":
        while True:
            user_path = input("Введите абсолютный или относительный путь к папке: ").strip()
            # Удаляем случайные кавычки, если пользователь скопировал путь как строку
            user_path = user_path.replace('"', '').replace("'", "")
            target_path = Path(user_path).resolve()
            if target_path.is_dir():
                return target_path
            print("[ОШИБКА] Указанный путь не существует или не является папкой. Попробуйте снова.")
    else:
        return Path.cwd()


def main():
    start = time.time()
    print("PDF -> JPG конвертер (оптимизирован для больших файлов)\n")

    # 1. Шаг выбора рабочей папки
    base_dir = select_working_dir()
    output_root = base_dir / "converted_jpg"
    print(f"\n[INFO] Рабочая папка: {base_dir}")
    print(f"[INFO] Папка для сохранения изображений: {output_root}\n")

    # 2. Шаг выбора режима конвертации
    print("Выберите режим:")
    print("1 - Конвертировать ВСЕ PDF в выбранной папке")
    print("2 - Конвертировать ОДИН конкретный PDF")
    mode = input("==> ").strip()

    if mode == "1":
        convert_all_pdfs(base_dir, output_root)
    elif mode == "2":
        name = input("Введите имя PDF (например: report.pdf): ").strip()
        convert_single_pdf(base_dir, output_root, name)
    else:
        print("Неверный режим.")

    print(f"\n--- Время выполнения: {time.time() - start:.2f} сек. ---")


if __name__ == "__main__":
    main()
