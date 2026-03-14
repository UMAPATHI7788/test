# PDF Hub

A full-stack **PDF utility hub** built with **Django REST Framework** (backend) and **React** (frontend — coming soon).

It exposes a clean REST API for the most common PDF operations:

| Operation | Endpoint | Method |
|---|---|---|
| Images → PDF | `/api/images-to-pdf/` | POST |
| PDF → Images | `/api/pdf-to-images/` | POST |
| Compress PDF | `/api/compress/` | POST |
| Merge PDFs | `/api/merge/` | POST |
| Split PDF | `/api/split/` | POST |
| Rotate PDF pages | `/api/rotate/` | POST |
| Extract text | `/api/extract-text/` | POST |
| Add watermark | `/api/watermark/` | POST |
| Conversion history | `/api/history/` | GET |

Interactive Swagger UI is available at **`/api/docs/`** when the server is running.

---

## Project Structure

```
pdf_hub/               ← Django project root (manage.py lives here)
├── pdf_hub/           ← Django project package (settings, urls, wsgi)
└── pdf_utils/         ← Django app
    ├── models.py      ← ConversionJob model
    ├── serializers.py ← DRF request/response serializers
    ├── views.py        ← APIView classes for every operation
    ├── urls.py        ← URL routing
    ├── tests.py       ← Test suite (20 tests)
    └── utils/         ← Pure-Python PDF utility functions
        ├── compressor.py
        ├── converter.py   (images→PDF, PDF→images)
        ├── merger.py
        ├── splitter.py
        ├── rotator.py
        ├── text_extractor.py
        └── watermark.py
requirements.txt
.gitignore
```

---

## Quick Start (Backend)

### 1 – Clone & enter the repo
```bash
git clone <repo-url>
cd test
```

### 2 – Create a virtual environment
```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
```

### 3 – Install dependencies
```bash
pip install -r requirements.txt
```

### 4 – Configure environment
```bash
cp backend/.env.example backend/.env
# Edit backend/.env and set SECRET_KEY (and any other values you need)
```

### 5 – Apply migrations & run
```bash
cd backend
python manage.py migrate
python manage.py runserver
```

The API is now live at **http://127.0.0.1:8000/**  
Swagger docs: **http://127.0.0.1:8000/api/docs/**

---

## API Usage Examples

### Convert images to PDF
```bash
curl -X POST http://localhost:8000/api/images-to-pdf/ \
  -F "images=@photo1.jpg" \
  -F "images=@photo2.png" \
  --output converted.pdf
```

### Compress a PDF
```bash
curl -X POST http://localhost:8000/api/compress/ \
  -F "pdf=@large.pdf" \
  -F "compression_level=high" \
  --output compressed.pdf
```

### Merge PDFs
```bash
curl -X POST http://localhost:8000/api/merge/ \
  -F "pdfs=@doc1.pdf" \
  -F "pdfs=@doc2.pdf" \
  --output merged.pdf
```

### Split a PDF (every page individually)
```bash
curl -X POST http://localhost:8000/api/split/ \
  -F "pdf=@multi_page.pdf" \
  --output split_pages.zip
```

### Rotate pages 90°
```bash
curl -X POST http://localhost:8000/api/rotate/ \
  -F "pdf=@doc.pdf" \
  -F "angle=90" \
  --output rotated.pdf
```

### Extract text
```bash
curl -X POST http://localhost:8000/api/extract-text/ \
  -F "pdf=@doc.pdf"
```

### Add watermark
```bash
curl -X POST http://localhost:8000/api/watermark/ \
  -F "pdf=@doc.pdf" \
  -F "text=CONFIDENTIAL" \
  -F "opacity=0.3" \
  --output watermarked.pdf
```

---

## Running Tests
```bash
cd backend
python manage.py test pdf_utils
```

---

## Dependencies

| Package | Purpose |
|---|---|
| Django | Web framework |
| djangorestframework | REST API toolkit |
| django-cors-headers | CORS support for React frontend |
| drf-spectacular | OpenAPI 3 schema + Swagger UI |
| PyPDF2 | PDF read / write / merge / split / rotate / watermark |
| Pillow | Image processing |
| img2pdf | High-quality image-to-PDF conversion |
| pikepdf | Low-level PDF compression |
| reportlab | PDF generation (watermark layer) |
| python-dotenv | `.env` file loading |

---

## Deployment Notes

1. Set `DEBUG=False` and provide a strong `SECRET_KEY` in your `.env`.
2. Set `ALLOWED_HOSTS` to your domain.
3. Use **Gunicorn** as the WSGI server behind **Nginx**.
4. Serve media files via Nginx (not Django) in production.
5. Use PostgreSQL in production by updating `DATABASES` in `settings.py`.

```bash
pip install gunicorn psycopg2-binary
gunicorn pdf_hub.wsgi:application --bind 0.0.0.0:8000
```
