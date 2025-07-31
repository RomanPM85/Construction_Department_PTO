import fitz  # PyMuPDF
import difflib

def extract_text_per_page(pdf_path):
    doc = fitz.open(pdf_path)
    pages_text = []
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text()
        pages_text.append(text)
    return pages_text

def compare_pdfs(pdf1, pdf2):
    text1 = extract_text_per_page(pdf1)
    text2 = extract_text_per_page(pdf2)

    max_pages = max(len(text1), len(text2))
    changed_pages = []

    for i in range(max_pages):
        t1 = text1[i] if i < len(text1) else ''
        t2 = text2[i] if i < len(text2) else ''
        if t1 != t2:
            changed_pages.append(i+1)  # страницы нумеруем с 1

    return changed_pages

if __name__ == "__main__":
    pdf_file_1 = "file1.pdf"
    pdf_file_2 = "file2.pdf"

    changes = compare_pdfs(pdf_file_1, pdf_file_2)
    if changes:
        print("Изменения найдены на страницах:", changes)
    else:
        print("Изменений не найдено")
