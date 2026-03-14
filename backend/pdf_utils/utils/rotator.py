"""PDF page rotation utility."""

import io

import PyPDF2


def rotate_pdf(input_bytes: bytes, angle: int, pages: list[int] | None = None) -> bytes:
    """
    Rotate pages in a PDF.

    Parameters
    ----------
    input_bytes:
        Raw bytes of the source PDF.
    angle:
        Rotation angle in degrees. Must be a multiple of 90 (90, 180, 270, -90, …).
    pages:
        1-based list of page numbers to rotate.  ``None`` rotates all pages.

    Returns
    -------
    bytes
        PDF bytes with the rotated pages.
    """
    if angle % 90 != 0:
        raise ValueError("Rotation angle must be a multiple of 90 degrees.")

    reader = PyPDF2.PdfReader(io.BytesIO(input_bytes))
    writer = PyPDF2.PdfWriter()

    for i, page in enumerate(reader.pages):
        page_num = i + 1  # 1-based
        if pages is None or page_num in pages:
            page.rotate(angle % 360)
        writer.add_page(page)

    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()
