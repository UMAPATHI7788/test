"""PDF watermark utility."""

import io

import PyPDF2
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas


def _create_watermark_pdf(text: str, opacity: float = 0.3, font_size: int = 48) -> bytes:
    """Generate an in-memory single-page watermark PDF."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    c.saveState()
    c.setFillColorRGB(0.5, 0.5, 0.5, alpha=opacity)
    c.setFont("Helvetica-Bold", font_size)
    c.translate(width / 2, height / 2)
    c.rotate(45)
    c.drawCentredString(0, 0, text)
    c.restoreState()
    c.save()
    buf.seek(0)
    return buf.read()


def add_watermark(
    input_bytes: bytes,
    watermark_text: str,
    opacity: float = 0.3,
    font_size: int = 48,
    pages: list[int] | None = None,
) -> bytes:
    """
    Overlay a diagonal text watermark on PDF pages.

    Parameters
    ----------
    input_bytes:
        Raw bytes of the source PDF.
    watermark_text:
        The text to stamp on each page.
    opacity:
        Watermark opacity between 0 (invisible) and 1 (fully opaque).
    font_size:
        Font size of the watermark text.
    pages:
        1-based page numbers to watermark.  ``None`` watermarks all pages.

    Returns
    -------
    bytes
        Watermarked PDF bytes.
    """
    watermark_bytes = _create_watermark_pdf(watermark_text, opacity, font_size)
    watermark_reader = PyPDF2.PdfReader(io.BytesIO(watermark_bytes))
    watermark_page = watermark_reader.pages[0]

    reader = PyPDF2.PdfReader(io.BytesIO(input_bytes))
    writer = PyPDF2.PdfWriter()

    for i, page in enumerate(reader.pages):
        page_num = i + 1
        if pages is None or page_num in pages:
            page.merge_page(watermark_page)
        writer.add_page(page)

    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()
