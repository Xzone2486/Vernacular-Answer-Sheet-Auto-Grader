FROM python:3.11-slim

# Install system dependencies for Tesseract OCR (Hindi) and image processing
# tesseract-ocr-hin installs the Hindi (Devanagari) trained data automatically.
# poppler-utils is needed by pdf2image for PDF → image conversion.
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-hin \
    libgl1 \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install CPU-only PyTorch first (smaller than full CUDA build), then other deps.
# sentence-transformers will use this pre-installed torch.
COPY requirements.txt .
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

# Create uploads directory
RUN mkdir -p /app/uploads

# Pre-download the sentence-transformer model at build time so it's cached
# in the Docker image and doesn't download on first request.
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')"

# Run uvicorn server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
