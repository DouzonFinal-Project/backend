# ==== Build stage (optional: slim enough to single-stage도 OK) ====
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# 시스템 의존성(필요시)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && rm -rf /var/lib/apt/lists/*

# 의존성
COPY requirements.txt .
RUN pip install -r requirements.txt

# 소스
COPY . .

# 8000 포트 공개
EXPOSE 8000

# uvicorn으로 기동
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
