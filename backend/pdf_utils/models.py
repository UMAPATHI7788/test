"""Models for the pdf_utils app."""

from django.db import models


class ConversionJob(models.Model):
    """Tracks a single PDF utility operation."""

    class OperationType(models.TextChoices):
        IMAGES_TO_PDF = "images_to_pdf", "Images → PDF"
        PDF_TO_IMAGES = "pdf_to_images", "PDF → Images"
        COMPRESS = "compress", "Compress PDF"
        MERGE = "merge", "Merge PDFs"
        SPLIT = "split", "Split PDF"
        ROTATE = "rotate", "Rotate PDF"
        EXTRACT_TEXT = "extract_text", "Extract Text"
        WATERMARK = "watermark", "Add Watermark"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    operation = models.CharField(max_length=20, choices=OperationType.choices)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.get_operation_display()} [{self.status}] @ {self.created_at:%Y-%m-%d %H:%M}"
