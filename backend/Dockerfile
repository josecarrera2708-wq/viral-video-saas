FROM python:3.11-slim

# ⚡ OPTIMIZADO PARA FREE TIER RAILWAY
# Instalaciones mínimas para máxima eficiencia

RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip cache purge

COPY main.py .

RUN mkdir -p /tmp/viral_videos

EXPOSE 8000

# ⚡ Limitar memoria y CPU
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# ⚡ Ejecutar con límites de recursos (1 worker = bajo CPU)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
