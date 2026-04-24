FROM python:3.13-slim

WORKDIR /app

COPY review-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ ./shared/
COPY review-service/ .

RUN mkdir -p uploads/reviews

EXPOSE 8004

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004"]
