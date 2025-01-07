from pypdf import PdfReader


def get_text_from_a_pdf_file(input_pdf):
    """
    return: all_text as a list
    """
    all_text = []
    with open(input_pdf, "rb"):
        reader = PdfReader(input_pdf)
        number_of_pages = len(reader.pages)
        for number in range(number_of_pages):
            page_object = reader.pages[number]
            text = page_object.extract_text()
            all_text.append(text)
    return all_text


def saves_text_to_a_file(page_text, out_file_docx):
    with open(out_file_docx, "w", encoding='utf-8') as doc_file:
        for each_page in page_text:
            doc_file.write(each_page)
    return out_file_docx


if __name__ == "__main__":
    pdf_file = "pdf_file.pdf"
    file_text = get_text_from_a_pdf_file(pdf_file)
    save_text = "saved_text.txt"
    for page in file_text:
        print(page)

    saves_text_to_a_file(file_text, save_text)
