FROM python:3.13-slim

WORKDIR /app

COPY restaurant-worker/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ ./shared/
COPY restaurant-worker/ .

CMD ["python", "worker.py"]
