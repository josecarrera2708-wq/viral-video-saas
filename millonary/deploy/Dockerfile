FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 MILLONARY_DATA=/data
WORKDIR /app
COPY requirements-live.txt .
RUN pip install --no-cache-dir -r requirements-live.txt
COPY src/__init__.py src/__init__.py
COPY src/core src/core
COPY src/live src/live
RUN useradd -m -u 10001 millonary && mkdir /data && chown millonary /data
USER millonary
VOLUME ["/data"]
CMD ["python", "-m", "src.live.runner", "--loop"]
