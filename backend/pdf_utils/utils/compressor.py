"""PDF compression utility using pikepdf."""

import io

import pikepdf


def compress_pdf(input_bytes: bytes, compression_level: str = "medium") -> bytes:
    """
    Compress a PDF file.

    Parameters
    ----------
    input_bytes:
        Raw bytes of the source PDF.
    compression_level:
        One of ``"low"``, ``"medium"`` (default), or ``"high"``.
        Higher means more aggressive compression (smaller file, potentially
        lower visual quality for embedded images).

    Returns
    -------
    bytes
        Compressed PDF bytes.
    """
    compress_streams = compression_level in ("medium", "high")
    recompress_images = compression_level == "high"
    image_quality = {"low": 85, "medium": 70, "high": 50}.get(compression_level, 70)

    with pikepdf.open(io.BytesIO(input_bytes)) as pdf:
        for page in pdf.pages:
            if recompress_images and "/Resources" in page:
                resources = page["/Resources"]
                if "/XObject" in resources:
                    for key in resources["/XObject"]:
                        xobj = resources["/XObject"][key]
                        if xobj.get("/Subtype") == "/Image":
                            try:
                                img_data = xobj.read_bytes()
                                from PIL import Image  # noqa: PLC0415

                                pil_img = Image.open(io.BytesIO(img_data))
                                if pil_img.mode in ("RGBA", "P"):
                                    pil_img = pil_img.convert("RGB")
                                out = io.BytesIO()
                                pil_img.save(out, format="JPEG", quality=image_quality)
                                xobj.write(out.getvalue(), filter=pikepdf.Name("/DCTDecode"))
                            except Exception:
                                pass  # Skip images that can't be recompressed

        output = io.BytesIO()
        pdf.save(
            output,
            compress_streams=compress_streams,
            recompress_flate=compress_streams,
            linearize=False,
        )
        return output.getvalue()
