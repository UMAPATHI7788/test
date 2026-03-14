"""PDF split utility."""

import io
import zipfile

import PyPDF2


def split_pdf(input_bytes: bytes, page_ranges: list[list[int]] | None = None) -> list[bytes]:
    """
    Split a PDF into multiple PDFs.

    Parameters
    ----------
    input_bytes:
        Raw bytes of the source PDF.
    page_ranges:
        Optional list of 1-based page ranges, e.g. ``[[1, 3], [4, 6]]``.
        If *None* every page is extracted individually.

    Returns
    -------
    list[bytes]
        One bytes object per output PDF.
    """
    reader = PyPDF2.PdfReader(io.BytesIO(input_bytes))
    total_pages = len(reader.pages)

    if page_ranges is None:
        # One PDF per page
        page_ranges = [[i + 1, i + 1] for i in range(total_pages)]

    results = []
    for start, end in page_ranges:
        # Clamp to valid range (1-based → 0-based)
        start = max(1, start)
        end = min(total_pages, end)
        writer = PyPDF2.PdfWriter()
        for page_num in range(start - 1, end):
            writer.add_page(reader.pages[page_num])
        buf = io.BytesIO()
        writer.write(buf)
        results.append(buf.getvalue())

    return results


def split_pdf_to_zip(input_bytes: bytes, page_ranges: list[list[int]] | None = None) -> bytes:
    """
    Split a PDF and return the individual PDFs packed into a ZIP archive.

    Returns
    -------
    bytes
        ZIP archive bytes.
    """
    pdfs = split_pdf(input_bytes, page_ranges)
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for idx, pdf_bytes in enumerate(pdfs, start=1):
            zf.writestr(f"page_{idx}.pdf", pdf_bytes)
    return zip_buffer.getvalue()
