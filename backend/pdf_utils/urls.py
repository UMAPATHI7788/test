"""URL routes for the pdf_utils app."""

from django.urls import path

from .views import (
    CompressPdfView,
    ConversionHistoryView,
    ExtractTextView,
    ImagesToPdfView,
    MergePdfsView,
    PdfToImagesView,
    RotatePdfView,
    SplitPdfView,
    WatermarkPdfView,
)

urlpatterns = [
    # Conversion endpoints
    path("images-to-pdf/", ImagesToPdfView.as_view(), name="images-to-pdf"),
    path("pdf-to-images/", PdfToImagesView.as_view(), name="pdf-to-images"),
    path("compress/", CompressPdfView.as_view(), name="compress-pdf"),
    path("merge/", MergePdfsView.as_view(), name="merge-pdfs"),
    path("split/", SplitPdfView.as_view(), name="split-pdf"),
    path("rotate/", RotatePdfView.as_view(), name="rotate-pdf"),
    path("extract-text/", ExtractTextView.as_view(), name="extract-text"),
    path("watermark/", WatermarkPdfView.as_view(), name="watermark-pdf"),
    # History
    path("history/", ConversionHistoryView.as_view(), name="conversion-history"),
]
