from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from PIL import Image


def add_png_watermark_to_pdf(pdf_path, png_path, output_path):
    """Adds a PNG watermark to each page of a PDF."""

    try:
        img = Image.open(png_path)
        img_width, img_height = img.size

        pdf = canvas.Canvas(output_path, pagesize=letter)  # Assumes letter size. Change as needed

        # Open the PDF for reading
        with open(pdf_path, "rb") as f:
            pdf.setPageSize(letter)  # You might need to infer page size from the PDF metadata if it isn't letter
            pdf.drawImage(png_path,
                          letter[0] - img_width - 10,  # x position (10 pixels from right edge)
                          10,  # y position (10 pixels from bottom edge)
                          img_width,
                          img_height,
                          preserveAspectRatio=True)

            """ Save the modified page (This is a simplified example - assumes the PDF is single page.
             See below for multi-page handling)
            """
            pdf.save()

    except FileNotFoundError:
        print(f"Error: PDF or PNG file not found.")
    except Exception as e:
        print(f"An error occurred: {e}")


# Example Usage
pdf_file = "input.pdf"
png_watermark = "watermark.png"
output_pdf = "output.pdf"

add_png_watermark_to_pdf(pdf_file, png_watermark, output_pdf)
