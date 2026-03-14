"""PDF merge utility."""

import io

import PyPDF2


def merge_pdfs(pdf_files: list[bytes]) -> bytes:
    """
    Merge multiple PDF files into a single PDF.

    Parameters
    ----------
    pdf_files:
        List of raw PDF bytes in the desired merge order.

    Returns
    -------
    bytes
        Merged PDF bytes.
    """
    merger = PyPDF2.PdfMerger()
    for pdf_bytes in pdf_files:
        merger.append(io.BytesIO(pdf_bytes))
    output = io.BytesIO()
    merger.write(output)
    merger.close()
    return output.getvalue()
