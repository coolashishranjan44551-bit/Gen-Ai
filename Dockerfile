# Container image for hosting the internal-document chatbot API + web widget
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System packages needed by unstructured document loaders (PDF, DOCX, etc.)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libmagic1 \
        poppler-utils \
        tesseract-ocr \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./requirements.txt
COPY bot/requirements.txt ./bot/requirements.txt

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt -r bot/requirements.txt

COPY bot ./bot
COPY README.md ./README.md

EXPOSE 8000
ENV PORT=8000

CMD ["sh", "-c", "uvicorn bot.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
