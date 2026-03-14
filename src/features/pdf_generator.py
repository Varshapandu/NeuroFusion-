import pdfkit
import os


def html_to_pdf(html_path):
    """Converts HTML report into a PDF file using wkhtmltopdf."""

    pdf_path = html_path.replace(".html", ".pdf")

    # If wkhtmltopdf is NOT in PATH, specify its full path here:
    # Example (Windows):
    # config = pdfkit.configuration(wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe")

    try:
        # Try default PATH first
        pdfkit.from_file(html_path, pdf_path)
        print("[INFO] PDF report generated at:", pdf_path)
    except OSError:
        print("[WARNING] wkhtmltopdf not found in PATH. Trying manual path...")

        # Try manual configuration
        wkhtml_path = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
        config = pdfkit.configuration(wkhtmltopdf=wkhtml_path)

        pdfkit.from_file(html_path, pdf_path, configuration=config)
        print("[INFO] PDF report generated using manual wkhtmltopdf path:", pdf_path)

    return pdf_path
