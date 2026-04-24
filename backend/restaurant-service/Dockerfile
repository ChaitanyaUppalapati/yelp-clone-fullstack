FROM python:3.13-slim

WORKDIR /app

COPY restaurant-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ ./shared/
COPY restaurant-service/ .

RUN mkdir -p uploads/restaurants

EXPOSE 8002

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
