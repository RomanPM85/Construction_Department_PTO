import pytesseract
from PIL import Image
import pandas as pd
from openpyxl import Workbook

# 1. Укажите путь к Tesseract OCR (если он не в системной переменной PATH)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Замените на свой путь

# 2. Функция для распознавания текста из изображения с использованием Tesseract OCR
def detect_table_from_image_tesseract(image_path):
    """Распознает текст из изображения, используя Tesseract OCR."""
    try:
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang='rus+eng')  # Укажите нужные языки
        return text
    except Exception as e:
        print(f"Ошибка при распознавании текста: {e}")
        return None

# 3. Функция для создания DataFrame (как в примере выше)
def create_dataframe(text):
    """Преобразует распознанный текст в DataFrame (очень упрощенно)."""
    if not text:
        return None

    lines = text.split('\n')
    # Внимание:  Это очень упрощенный пример.  Для реальных таблиц потребуется
    #           более сложная логика разбиения текста на столбцы и строки.
    df = pd.DataFrame(lines) # Создаем DataFrame из строк
    return df

# 4. Функция для сохранения DataFrame в XLSX-файл (как в примере выше)
def save_to_excel(df, output_file):
    """Сохраняет DataFrame в XLSX-файл."""
    if df is None:
        print("Нет данных для сохранения.")
        return

    try:
        df.to_excel(output_file, index=False)
        print(f"Таблица успешно сохранена в {output_file}")
    except Exception as e:
        print(f"Ошибка при сохранении в Excel: {e}")

# 5. Основная часть программы
if __name__ == "__main__":
    input_image = "input_table1.png"  # Замените на имя вашего PNG-файла
    output_excel = "input_table1.xlsx" # Замените на имя выходного XLSX-файла

    # Распознаем текст из изображения
    recognized_text = detect_table_from_image_tesseract(input_image)

    # Создаем DataFrame
    df = create_dataframe(recognized_text)

    # Сохраняем DataFrame в XLSX-файл
    save_to_excel(df, output_excel)
