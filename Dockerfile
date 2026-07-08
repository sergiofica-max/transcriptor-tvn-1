FROM python:3.10-slim

WORKDIR /app

# Instalar dependencias esenciales del sistema
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# 1. Copiar requerimientos desde la subcarpeta e instalar
COPY TVN-TRANSCRIPTOR/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Copiar todo el código de la subcarpeta a /app
COPY TVN-TRANSCRIPTOR/ .

# 3. Puerto dinámico para Railway
CMD uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}
Fix: limpiar líneas duplicadas en Dockerfile"
