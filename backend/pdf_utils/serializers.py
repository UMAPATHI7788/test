"""Serializers for pdf_utils app."""

from rest_framework import serializers

from .models import ConversionJob


# ──────────────────────────────────────────────
# Request serializers (validate incoming data)
# ──────────────────────────────────────────────

class ImagesToPdfSerializer(serializers.Serializer):
    """One or more images to be converted to a single PDF."""

    images = serializers.ListField(
        child=serializers.ImageField(),
        min_length=1,
        help_text="One or more image files (JPEG, PNG, BMP, TIFF, WebP).",
    )


class PdfToImagesSerializer(serializers.Serializer):
    """A PDF to be rendered as images."""

    pdf = serializers.FileField(help_text="The PDF file to convert.")
    dpi = serializers.IntegerField(
        default=150,
        min_value=72,
        max_value=600,
        help_text="Rendering resolution in DPI (72–600, default 150).",
    )
    format = serializers.ChoiceField(
        choices=["PNG", "JPEG"],
        default="PNG",
        help_text="Output image format.",
    )


class CompressPdfSerializer(serializers.Serializer):
    """A PDF to be compressed."""

    pdf = serializers.FileField(help_text="The PDF file to compress.")
    compression_level = serializers.ChoiceField(
        choices=["low", "medium", "high"],
        default="medium",
        help_text="Compression level: low, medium, or high.",
    )


class MergePdfsSerializer(serializers.Serializer):
    """Multiple PDFs to be merged in order."""

    pdfs = serializers.ListField(
        child=serializers.FileField(),
        min_length=2,
        help_text="Two or more PDF files to merge (in order).",
    )


class PageRangeField(serializers.ListField):
    """Validates a single page range [start, end]."""

    child = serializers.IntegerField(min_value=1)

    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        if len(data) != 2:
            raise serializers.ValidationError("Each range must be [start, end].")
        if data[0] > data[1]:
            raise serializers.ValidationError("start must be ≤ end.")
        return data


class SplitPdfSerializer(serializers.Serializer):
    """A PDF to be split."""

    pdf = serializers.FileField(help_text="The PDF file to split.")
    page_ranges = serializers.ListField(
        child=PageRangeField(),
        required=False,
        allow_empty=True,
        help_text=(
            "Optional list of [start, end] page ranges (1-based). "
            "Leave empty to split every page individually."
        ),
    )


class RotatePdfSerializer(serializers.Serializer):
    """A PDF with rotation options."""

    pdf = serializers.FileField(help_text="The PDF file to rotate.")
    angle = serializers.ChoiceField(
        choices=[90, 180, 270, -90, -180, -270],
        help_text="Rotation angle in degrees (must be a multiple of 90).",
    )
    pages = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        allow_empty=True,
        help_text="1-based page numbers to rotate. Leave empty to rotate all pages.",
    )


class ExtractTextSerializer(serializers.Serializer):
    """A PDF whose text should be extracted."""

    pdf = serializers.FileField(help_text="The PDF file to extract text from.")


class WatermarkPdfSerializer(serializers.Serializer):
    """A PDF to be watermarked."""

    pdf = serializers.FileField(help_text="The PDF file to watermark.")
    text = serializers.CharField(
        max_length=100,
        help_text="Watermark text.",
    )
    opacity = serializers.FloatField(
        default=0.3,
        min_value=0.0,
        max_value=1.0,
        help_text="Watermark opacity (0.0–1.0, default 0.3).",
    )
    font_size = serializers.IntegerField(
        default=48,
        min_value=8,
        max_value=200,
        help_text="Font size of the watermark text (default 48).",
    )
    pages = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        allow_empty=True,
        help_text="1-based page numbers to watermark. Leave empty to watermark all pages.",
    )


# ──────────────────────────────────────────────
# Response / model serializers
# ──────────────────────────────────────────────

class ConversionJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConversionJob
        fields = ["id", "operation", "status", "error_message", "created_at"]
        read_only_fields = fields


class ExtractedTextSerializer(serializers.Serializer):
    total_pages = serializers.IntegerField()
    pages = serializers.ListField(
        child=serializers.DictField()
    )
