FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

COPY TVN-TRANSCRIPTOR/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY TVN-TRANSCRIPTOR/ .

EXPOSE 8000

CMD ["python", "app.py"]
