FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Copy requirements first for better caching
COPY requirements.txt /tmp/req.txt
RUN pip install -r /tmp/req.txt

# Copy shared kits first
COPY kits ./kits

# Copy app code last
COPY apps/worker ./apps/worker

CMD ["python", "-m", "apps.worker.worker"]

