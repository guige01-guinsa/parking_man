FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

RUN mkdir -p /data /uploads

ENV PARKING_DB_PATH=/data/parking.db
ENV PARKING_UPLOAD_DIR=/uploads
ENV PARKING_ROOT_PATH=/parking

EXPOSE 8011

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8011", "--proxy-headers", "--forwarded-allow-ips", "*"]
