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
COPY apps/api ./apps/api

EXPOSE 8000

CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

