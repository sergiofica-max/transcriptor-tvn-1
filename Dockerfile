FROM python:3.10-slim

WORKDIR /app

# Instalar dependencias del sistema esenciales
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copiar e instalar requerimientos
COPY TVN-TRANSCRIPTOR/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente
COPY TVN-TRANSCRIPTOR/ .

# Exponer el puerto que Railway asigna automáticamente
EXPOSE 8000

# Comando para ejecutar la aplicación
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

