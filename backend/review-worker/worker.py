"""
Review Worker — consumes review.* Kafka events, updates restaurant avg_rating in MongoDB,
and publishes booking.status back to notify frontend-facing services of processing outcome.
"""
import os
import json
import asyncio
import logging
from confluent_kafka import Consumer, Producer, KafkaError
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/yelp_db")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("review-worker")

_producer: Producer | None = None


def get_producer() -> Producer:
    global _producer
    if _producer is None:
        _producer = Producer({"bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS})
    return _producer


def publish_status(review_id: str, status: str, detail: str = ""):
    payload = json.dumps({
        "review_id": review_id,
        "status": status,   # "confirmed" | "failed"
        "detail": detail,
    }).encode("utf-8")
    get_producer().produce("booking.status", key=review_id.encode(), value=payload)
    get_producer().poll(0)
    log.info("Published booking.status: review_id=%s status=%s", review_id, status)


def get_db():
    client = AsyncIOMotorClient(MONGO_URL)
    db_name = MONGO_URL.rsplit("/", 1)[-1].split("?")[0] or "yelp_db"
    return client[db_name]


async def recalculate_avg_rating(db, restaurant_id: str):
    pipeline = [
        {"$match": {"restaurant_id": restaurant_id}},
        {"$group": {"_id": None, "avg": {"$avg": "$rating"}, "count": {"$sum": 1}}},
    ]
    result = await db.reviews.aggregate(pipeline).to_list(1)
    if result:
        avg = round(result[0]["avg"], 2)
        count = result[0]["count"]
    else:
        avg = 0.0
        count = 0

    await db.restaurants.update_one(
        {"_id": ObjectId(restaurant_id)},
        {"$set": {"avg_rating": avg, "review_count": count}},
    )
    log.info("Updated restaurant %s: avg_rating=%.2f, review_count=%d", restaurant_id, avg, count)


async def process_event(db, topic: str, data: dict):
    restaurant_id = data.get("restaurant_id")
    review_id = data.get("review_id", "unknown")

    if not restaurant_id:
        return

    if topic in ("review.created", "review.updated", "review.deleted"):
        await recalculate_avg_rating(db, restaurant_id)
        # Publish confirmation back to frontend-facing services
        action = topic.split(".")[1]   # created | updated | deleted
        publish_status(review_id, "confirmed", f"Review {action} and ratings updated.")


async def run():
    db = get_db()
    consumer = Consumer({
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "group.id": "review-worker-group",
        "auto.offset.reset": "earliest",
    })
    consumer.subscribe(["review.created", "review.updated", "review.deleted"])
    log.info("Review worker started, waiting for messages...")

    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None:
                await asyncio.sleep(0.1)
                continue
            if msg.error():
                if msg.error().code() != KafkaError._PARTITION_EOF:
                    log.error("Kafka error: %s", msg.error())
                continue

            topic = msg.topic()
            try:
                data = json.loads(msg.value().decode("utf-8"))
                log.info("Received %s: %s", topic, data)
                await process_event(db, topic, data)
            except Exception as exc:
                log.exception("Failed to process %s: %s", topic, exc)
                publish_status(
                    data.get("review_id", "unknown"), "failed", str(exc)
                )
    finally:
        consumer.close()


if __name__ == "__main__":
    asyncio.run(run())
