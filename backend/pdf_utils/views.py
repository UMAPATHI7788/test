"""API views for all PDF utility operations."""

import io
import zipfile

from django.http import HttpResponse
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ConversionJob
from .serializers import (
    CompressPdfSerializer,
    ConversionJobSerializer,
    ExtractedTextSerializer,
    ExtractTextSerializer,
    ImagesToPdfSerializer,
    MergePdfsSerializer,
    PdfToImagesSerializer,
    RotatePdfSerializer,
    SplitPdfSerializer,
    WatermarkPdfSerializer,
)
from .utils import (
    add_watermark,
    compress_pdf,
    extract_text_from_pdf,
    images_to_pdf,
    merge_pdfs,
    pdf_to_images,
    rotate_pdf,
    split_pdf_to_zip,
)


def _log_job(operation: str, success: bool, error: str = "") -> ConversionJob:
    """Create a ConversionJob record."""
    return ConversionJob.objects.create(
        operation=operation,
        status=ConversionJob.Status.COMPLETED if success else ConversionJob.Status.FAILED,
        error_message=error,
    )


# ──────────────────────────────────────────────
# Images → PDF
# ──────────────────────────────────────────────

class ImagesToPdfView(APIView):
    """Convert one or more images to a single PDF file."""

    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        request=ImagesToPdfSerializer,
        responses={200: OpenApiResponse(description="PDF file")},
        summary="Convert images to PDF",
        description=(
            "Upload one or more image files (JPEG, PNG, BMP, TIFF, WebP) and "
            "receive a single merged PDF in return."
        ),
    )
    def post(self, request):
        serializer = ImagesToPdfSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        image_files = [f.read() for f in request.FILES.getlist("images")]
        try:
            pdf_bytes = images_to_pdf(image_files)
            _log_job(ConversionJob.OperationType.IMAGES_TO_PDF, success=True)
            response = HttpResponse(pdf_bytes, content_type="application/pdf")
            response["Content-Disposition"] = 'attachment; filename="converted.pdf"'
            return response
        except Exception as exc:
            _log_job(ConversionJob.OperationType.IMAGES_TO_PDF, success=False, error=str(exc))
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


# ──────────────────────────────────────────────
# PDF → Images
# ──────────────────────────────────────────────

class PdfToImagesView(APIView):
    """Convert each page of a PDF to an image."""

    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        request=PdfToImagesSerializer,
        responses={200: OpenApiResponse(description="ZIP archive of images")},
        summary="Convert PDF to images",
        description=(
            "Upload a PDF and receive a ZIP archive containing one image "
            "(PNG or JPEG) per page."
        ),
    )
    def post(self, request):
        serializer = PdfToImagesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        pdf_bytes = request.FILES["pdf"].read()
        dpi = serializer.validated_data["dpi"]
        fmt = serializer.validated_data["format"]

        try:
            images = pdf_to_images(pdf_bytes, dpi=dpi, fmt=fmt)
            _log_job(ConversionJob.OperationType.PDF_TO_IMAGES, success=True)

            ext = fmt.lower()
            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for i, img_bytes in enumerate(images, start=1):
                    zf.writestr(f"page_{i}.{ext}", img_bytes)

            response = HttpResponse(zip_buf.getvalue(), content_type="application/zip")
            response["Content-Disposition"] = 'attachment; filename="pdf_images.zip"'
            return response
        except Exception as exc:
            _log_job(ConversionJob.OperationType.PDF_TO_IMAGES, success=False, error=str(exc))
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


# ──────────────────────────────────────────────
# Compress PDF
# ──────────────────────────────────────────────

class CompressPdfView(APIView):
    """Compress a PDF file."""

    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        request=CompressPdfSerializer,
        responses={200: OpenApiResponse(description="Compressed PDF file")},
        summary="Compress a PDF",
        description="Upload a PDF and receive a compressed version.",
    )
    def post(self, request):
        serializer = CompressPdfSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        pdf_bytes = request.FILES["pdf"].read()
        level = serializer.validated_data["compression_level"]

        try:
            compressed = compress_pdf(pdf_bytes, compression_level=level)
            _log_job(ConversionJob.OperationType.COMPRESS, success=True)
            response = HttpResponse(compressed, content_type="application/pdf")
            response["Content-Disposition"] = 'attachment; filename="compressed.pdf"'
            return response
        except Exception as exc:
            _log_job(ConversionJob.OperationType.COMPRESS, success=False, error=str(exc))
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


# ──────────────────────────────────────────────
# Merge PDFs
# ──────────────────────────────────────────────

class MergePdfsView(APIView):
    """Merge multiple PDF files into one."""

    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        request=MergePdfsSerializer,
        responses={200: OpenApiResponse(description="Merged PDF file")},
        summary="Merge PDFs",
        description="Upload two or more PDF files and receive them merged into a single PDF.",
    )
    def post(self, request):
        serializer = MergePdfsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        pdf_files = [f.read() for f in request.FILES.getlist("pdfs")]
        try:
            merged = merge_pdfs(pdf_files)
            _log_job(ConversionJob.OperationType.MERGE, success=True)
            response = HttpResponse(merged, content_type="application/pdf")
            response["Content-Disposition"] = 'attachment; filename="merged.pdf"'
            return response
        except Exception as exc:
            _log_job(ConversionJob.OperationType.MERGE, success=False, error=str(exc))
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


# ──────────────────────────────────────────────
# Split PDF
# ──────────────────────────────────────────────

class SplitPdfView(APIView):
    """Split a PDF into multiple PDFs."""

    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        request=SplitPdfSerializer,
        responses={200: OpenApiResponse(description="ZIP archive of PDFs")},
        summary="Split a PDF",
        description=(
            "Upload a PDF and optionally specify page ranges. "
            "Receive a ZIP archive containing the split PDFs."
        ),
    )
    def post(self, request):
        serializer = SplitPdfSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        pdf_bytes = request.FILES["pdf"].read()
        page_ranges = serializer.validated_data.get("page_ranges") or None

        try:
            zip_bytes = split_pdf_to_zip(pdf_bytes, page_ranges)
            _log_job(ConversionJob.OperationType.SPLIT, success=True)
            response = HttpResponse(zip_bytes, content_type="application/zip")
            response["Content-Disposition"] = 'attachment; filename="split_pages.zip"'
            return response
        except Exception as exc:
            _log_job(ConversionJob.OperationType.SPLIT, success=False, error=str(exc))
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


# ──────────────────────────────────────────────
# Rotate PDF
# ──────────────────────────────────────────────

class RotatePdfView(APIView):
    """Rotate pages of a PDF."""

    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        request=RotatePdfSerializer,
        responses={200: OpenApiResponse(description="Rotated PDF file")},
        summary="Rotate PDF pages",
        description=(
            "Upload a PDF and specify a rotation angle (multiples of 90°). "
            "Optionally target specific pages."
        ),
    )
    def post(self, request):
        serializer = RotatePdfSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        pdf_bytes = request.FILES["pdf"].read()
        angle = int(serializer.validated_data["angle"])
        pages = serializer.validated_data.get("pages") or None

        try:
            rotated = rotate_pdf(pdf_bytes, angle=angle, pages=pages)
            _log_job(ConversionJob.OperationType.ROTATE, success=True)
            response = HttpResponse(rotated, content_type="application/pdf")
            response["Content-Disposition"] = 'attachment; filename="rotated.pdf"'
            return response
        except Exception as exc:
            _log_job(ConversionJob.OperationType.ROTATE, success=False, error=str(exc))
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


# ──────────────────────────────────────────────
# Extract Text
# ──────────────────────────────────────────────

class ExtractTextView(APIView):
    """Extract plain text from a PDF."""

    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        request=ExtractTextSerializer,
        responses={200: ExtractedTextSerializer},
        summary="Extract text from a PDF",
        description="Upload a PDF and receive a JSON response with extracted text per page.",
    )
    def post(self, request):
        serializer = ExtractTextSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        pdf_bytes = request.FILES["pdf"].read()
        try:
            result = extract_text_from_pdf(pdf_bytes)
            _log_job(ConversionJob.OperationType.EXTRACT_TEXT, success=True)
            return Response(result)
        except Exception as exc:
            _log_job(ConversionJob.OperationType.EXTRACT_TEXT, success=False, error=str(exc))
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


# ──────────────────────────────────────────────
# Watermark PDF
# ──────────────────────────────────────────────

class WatermarkPdfView(APIView):
    """Add a text watermark to a PDF."""

    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        request=WatermarkPdfSerializer,
        responses={200: OpenApiResponse(description="Watermarked PDF file")},
        summary="Add watermark to PDF",
        description=(
            "Upload a PDF and provide watermark text. "
            "Receive the PDF with a diagonal text watermark on each page."
        ),
    )
    def post(self, request):
        serializer = WatermarkPdfSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        pdf_bytes = request.FILES["pdf"].read()
        text = serializer.validated_data["text"]
        opacity = serializer.validated_data["opacity"]
        font_size = serializer.validated_data["font_size"]
        pages = serializer.validated_data.get("pages") or None

        try:
            watermarked = add_watermark(pdf_bytes, text, opacity=opacity, font_size=font_size, pages=pages)
            _log_job(ConversionJob.OperationType.WATERMARK, success=True)
            response = HttpResponse(watermarked, content_type="application/pdf")
            response["Content-Disposition"] = 'attachment; filename="watermarked.pdf"'
            return response
        except Exception as exc:
            _log_job(ConversionJob.OperationType.WATERMARK, success=False, error=str(exc))
            return Response({"error": str(exc)}, status=status.HTTP_400_BAD_REQUEST)


# ──────────────────────────────────────────────
# Conversion History
# ──────────────────────────────────────────────

class ConversionHistoryView(APIView):
    """List recent conversion jobs."""

    @extend_schema(
        responses={200: ConversionJobSerializer(many=True)},
        summary="Conversion history",
        description="Returns the 50 most recent conversion jobs.",
    )
    def get(self, request):
        jobs = ConversionJob.objects.all()[:50]
        serializer = ConversionJobSerializer(jobs, many=True)
        return Response(serializer.data)

