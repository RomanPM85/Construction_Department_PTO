from PyPDF2 import PdfReader, PdfWriter
from pathlib import Path


pdf_file = Path.cwd() / "input.pdf"
watermark = Path.cwd() / "watermark.pdf"
merged = Path.cwd() / "output_watermark.pdf"

with open(pdf_file, "rb") as input_file, open(watermark, "rb") as watermark_file:
    input_pdf = PdfReader(input_file)  # opens the original file

    watermark_pdf = PdfReader(watermark)  # opens the watermarked file
    watermark_page = watermark_pdf.pages[0]  # gets the first page of the watermark

    output = PdfWriter()  # this will hold the new pages

    for i in range(len(input_pdf.pages)):  # go through each page
        pdf_page = input_pdf.pages[i]
        pdf_page.merge_page(watermark_page)  # combine the watermark and the current page
        output.add_page(pdf_page)

    with open(merged, "wb") as merged_file:
        output.write(merged_file)
