import fitz  # PyMuPDF

def compress_pdf(input_path, output_path, zoom_x=0.8, zoom_y=0.8, rotation=0):
    doc = fitz.open(input_path)
    new_doc = fitz.open()

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        # Создаем уменьшенную страницу как pixmap
        mat = fitz.Matrix(zoom_x, zoom_y).prerotate(rotation)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        # Создаем новую страницу с размерами pixmap
        new_page = new_doc.new_page(width=pix.width, height=pix.height)
        new_page.insert_image(new_page.rect, pixmap=pix)

    new_doc.save(output_path, deflate=True)
    new_doc.close()
    doc.close()

# Пример использования
compress_pdf("Scane_.pdf", "compressed_output.pdf")
