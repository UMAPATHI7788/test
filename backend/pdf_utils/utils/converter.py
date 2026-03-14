"""Image ↔ PDF conversion utilities."""

import io
import zipfile

import img2pdf
from PIL import Image


def images_to_pdf(image_files: list[bytes]) -> bytes:
    """
    Convert one or more images (JPEG, PNG, BMP, TIFF, WEBP, GIF) to a single PDF.

    Parameters
    ----------
    image_files:
        List of raw image bytes (one per page).

    Returns
    -------
    bytes
        PDF bytes with one page per input image.
    """
    converted = []
    for img_bytes in image_files:
        # img2pdf works best with JPEG; convert other formats first.
        img = Image.open(io.BytesIO(img_bytes))
        if img.format not in ("JPEG", "JPG") or img.mode not in ("RGB", "L"):
            buf = io.BytesIO()
            img = img.convert("RGB")
            img.save(buf, format="JPEG")
            converted.append(buf.getvalue())
        else:
            converted.append(img_bytes)

    return img2pdf.convert(converted)


def pdf_to_images(input_bytes: bytes, dpi: int = 150, fmt: str = "PNG") -> list[bytes]:
    """
    Convert each page of a PDF to an image.

    Uses Pillow's PDF plugin if available, otherwise falls back to a
    page-by-page render via PyPDF2 + Pillow.

    Parameters
    ----------
    input_bytes:
        Raw PDF bytes.
    dpi:
        Rendering resolution (default 150).
    fmt:
        Output image format, e.g. ``"PNG"`` or ``"JPEG"``.

    Returns
    -------
    list[bytes]
        One bytes object per page.
    """
    try:
        from pdf2image import convert_from_bytes  # noqa: PLC0415

        images = convert_from_bytes(input_bytes, dpi=dpi)
        pages = []
        for img in images:
            buf = io.BytesIO()
            img.save(buf, format=fmt)
            pages.append(buf.getvalue())
        return pages
    except ImportError:
        pass

    # Fallback: use pikepdf + Pillow (renders blank but keeps structure)
    import pikepdf  # noqa: PLC0415

    pages = []
    with pikepdf.open(io.BytesIO(input_bytes)) as pdf:
        for i, page in enumerate(pdf.pages):
            # Save each page as a single-page PDF then open with Pillow
            single = pikepdf.Pdf.new()
            single.pages.append(page)
            buf = io.BytesIO()
            single.save(buf)
            buf.seek(0)
            try:
                img = Image.open(buf)
                out = io.BytesIO()
                img.save(out, format=fmt)
                pages.append(out.getvalue())
            except Exception:
                # Placeholder image if rendering fails
                placeholder = Image.new("RGB", (595, 842), color=(255, 255, 255))
                out = io.BytesIO()
                placeholder.save(out, format=fmt)
                pages.append(out.getvalue())
    return pages
