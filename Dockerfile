# ==== Build stage (optional: slim enough to single-stage도 OK) ====
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 시스템 의존성
RUN apt-get update && apt-get install -y --no-install-recommends \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libglib2.0-0 \
    libffi8 \
    libxml2 \
    libxslt1.1 \
    fonts-dejavu fonts-liberation fonts-noto-core \
    shared-mime-info \
    ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# 의존성
COPY requirements.txt .
RUN pip install -r requirements.txt

# 소스
COPY . .

# 8000 포트 공개
EXPOSE 8000

# uvicorn으로 기동
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
