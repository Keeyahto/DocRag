FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY apps/api/requirements.txt /tmp/req.txt
RUN pip install --no-cache-dir -r /tmp/req.txt

# Copy shared kits and app code
COPY kits ./kits
COPY apps/api ./apps/api

EXPOSE 8000

CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

