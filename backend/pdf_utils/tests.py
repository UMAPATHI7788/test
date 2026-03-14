"""Tests for the pdf_utils app."""

import io
import zipfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from PIL import Image
from reportlab.pdfgen import canvas
from rest_framework import status
from rest_framework.test import APIClient

from .models import ConversionJob


def _make_jpeg_bytes() -> bytes:
    """Create a minimal valid JPEG image in memory."""
    img = Image.new("RGB", (100, 100), color=(255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def _make_png_bytes() -> bytes:
    """Create a minimal valid PNG image in memory."""
    img = Image.new("RGB", (100, 100), color=(0, 255, 0))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _make_pdf_bytes(text: str = "Hello PDF", pages: int = 2) -> bytes:
    """Create a minimal valid PDF with *pages* pages using reportlab."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    for i in range(pages):
        c.drawString(100, 750, f"{text} – page {i + 1}")
        c.showPage()
    c.save()
    return buf.getvalue()


def _jpeg_upload(name: str = "test.jpg") -> SimpleUploadedFile:
    return SimpleUploadedFile(name, _make_jpeg_bytes(), content_type="image/jpeg")


def _png_upload(name: str = "test.png") -> SimpleUploadedFile:
    return SimpleUploadedFile(name, _make_png_bytes(), content_type="image/png")


def _pdf_upload(text: str = "Hello PDF", pages: int = 2, name: str = "test.pdf") -> SimpleUploadedFile:
    return SimpleUploadedFile(name, _make_pdf_bytes(text, pages), content_type="application/pdf")


class ImagesToPdfViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("images-to-pdf")

    def test_single_jpeg(self):
        response = self.client.post(
            self.url,
            {"images": [_jpeg_upload()]},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn(b"%PDF", response.content[:10])

    def test_multiple_images(self):
        response = self.client.post(
            self.url,
            {"images": [_jpeg_upload("a.jpg"), _png_upload("b.png")]},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(b"%PDF", response.content[:10])

    def test_missing_images_returns_400(self):
        response = self.client.post(self.url, {}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_job_created(self):
        before = ConversionJob.objects.count()
        self.client.post(self.url, {"images": [_jpeg_upload()]}, format="multipart")
        self.assertEqual(ConversionJob.objects.count(), before + 1)


class CompressPdfViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("compress-pdf")

    def test_compress_low(self):
        response = self.client.post(
            self.url,
            {"pdf": _pdf_upload(), "compression_level": "low"},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(b"%PDF", response.content[:10])

    def test_compress_medium(self):
        response = self.client.post(
            self.url,
            {"pdf": _pdf_upload(), "compression_level": "medium"},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_compress_high(self):
        response = self.client.post(
            self.url,
            {"pdf": _pdf_upload(), "compression_level": "high"},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_level_returns_400(self):
        response = self.client.post(
            self.url,
            {"pdf": _pdf_upload(), "compression_level": "ultra"},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class MergePdfsViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("merge-pdfs")

    def test_merge_two_pdfs(self):
        response = self.client.post(
            self.url,
            {"pdfs": [_pdf_upload("First"), _pdf_upload("Second")]},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(b"%PDF", response.content[:10])

    def test_single_pdf_returns_400(self):
        response = self.client.post(
            self.url,
            {"pdfs": [_pdf_upload()]},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class SplitPdfViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("split-pdf")

    def test_split_into_individual_pages(self):
        response = self.client.post(
            self.url,
            {"pdf": _pdf_upload(pages=3)},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/zip")
        zf = zipfile.ZipFile(io.BytesIO(response.content))
        self.assertEqual(len(zf.namelist()), 3)

    def test_split_with_page_ranges_utility(self):
        """Test the split utility directly with page ranges."""
        from .utils.splitter import split_pdf  # noqa: PLC0415

        parts = split_pdf(_make_pdf_bytes(pages=4), [[1, 2], [3, 4]])
        self.assertEqual(len(parts), 2)
        for part in parts:
            self.assertIn(b"%PDF", part[:10])


class RotatePdfViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("rotate-pdf")

    def test_rotate_all_pages(self):
        response = self.client.post(
            self.url,
            {"pdf": _pdf_upload(pages=2), "angle": "90"},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(b"%PDF", response.content[:10])

    def test_invalid_angle_returns_400(self):
        response = self.client.post(
            self.url,
            {"pdf": _pdf_upload(), "angle": "45"},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ExtractTextViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("extract-text")

    def test_extract_text(self):
        response = self.client.post(
            self.url,
            {"pdf": _pdf_upload("Sample text")},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("total_pages", data)
        self.assertIn("pages", data)
        self.assertEqual(data["total_pages"], 2)

    def test_missing_pdf_returns_400(self):
        response = self.client.post(self.url, {}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class WatermarkPdfViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("watermark-pdf")

    def test_add_watermark(self):
        response = self.client.post(
            self.url,
            {"pdf": _pdf_upload(), "text": "CONFIDENTIAL"},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(b"%PDF", response.content[:10])

    def test_text_required(self):
        response = self.client.post(
            self.url,
            {"pdf": _pdf_upload()},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ConversionHistoryViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse("conversion-history")

    def test_returns_list(self):
        ConversionJob.objects.create(
            operation=ConversionJob.OperationType.COMPRESS,
            status=ConversionJob.Status.COMPLETED,
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.json(), list)
        self.assertGreaterEqual(len(response.json()), 1)


class ConversionJobModelTest(TestCase):
    def test_str(self):
        job = ConversionJob.objects.create(
            operation=ConversionJob.OperationType.MERGE,
            status=ConversionJob.Status.COMPLETED,
        )
        self.assertIn("Merge", str(job))
