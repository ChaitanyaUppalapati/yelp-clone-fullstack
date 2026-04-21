FROM python:3.13-slim

WORKDIR /app

COPY user-worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ ./shared/
COPY user-worker/ .

CMD ["python", "worker.py"]
