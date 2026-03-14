"""PDF text extraction utility."""

import io

import PyPDF2


def extract_text_from_pdf(input_bytes: bytes) -> dict:
    """
    Extract plain text from each page of a PDF.

    Parameters
    ----------
    input_bytes:
        Raw bytes of the source PDF.

    Returns
    -------
    dict
        ``{"total_pages": int, "pages": [{"page": int, "text": str}, ...]}``
    """
    reader = PyPDF2.PdfReader(io.BytesIO(input_bytes))
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        pages.append({"page": i + 1, "text": text.strip()})

    return {"total_pages": len(reader.pages), "pages": pages}
