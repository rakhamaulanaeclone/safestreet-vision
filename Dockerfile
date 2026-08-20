FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir onnxruntime

COPY backend/ /app/
COPY runs/ /runs/

# Railway dan PaaS lain menyuntikkan port melalui environment variable PORT (default 8000)
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
