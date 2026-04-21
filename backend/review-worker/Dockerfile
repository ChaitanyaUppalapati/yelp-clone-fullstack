FROM python:3.13-slim

WORKDIR /app

COPY review-worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ ./shared/
COPY review-worker/ .

CMD ["python", "worker.py"]
