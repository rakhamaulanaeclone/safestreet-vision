FROM python:3.11-slim

# Mencegah Python membuat file .pyc dan memastikan log terminal langsung tampil
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Menginstal sistem dependencies untuk OpenCV (wajib di Linux slim)
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Menyalin file dependencies dan menginstal library python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Tambahkan onnxruntime versi CPU agar Ultralytics dapat memproses model ONNX
RUN pip install --no-cache-dir onnxruntime

# Menyalin seluruh kode backend
COPY . .

# Menjalankan uvicorn server di port 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
