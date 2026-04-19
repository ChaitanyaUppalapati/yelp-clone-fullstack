"""
Restaurant Worker — consumes restaurant.* Kafka events for async processing (logging, notifications).
"""
import os
import json
import asyncio
import logging
from confluent_kafka import Consumer, KafkaError

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("restaurant-worker")


async def process_event(topic: str, data: dict):
    if topic == "restaurant.created":
        log.info("New restaurant listed: id=%s owner=%s", data.get("restaurant_id"), data.get("owner_id"))
    elif topic == "restaurant.updated":
        log.info("Restaurant updated: id=%s", data.get("restaurant_id"))
    elif topic == "restaurant.claimed":
        log.info("Restaurant claimed: id=%s new_owner=%s", data.get("restaurant_id"), data.get("new_owner_id"))


async def run():
    consumer = Consumer({
        "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
        "group.id": "restaurant-worker-group",
        "auto.offset.reset": "earliest",
    })
    consumer.subscribe(["restaurant.created", "restaurant.updated", "restaurant.claimed"])
    log.info("Restaurant worker started, waiting for messages...")

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
                await process_event(topic, data)
            except Exception as exc:
                log.exception("Failed to process %s: %s", topic, exc)
    finally:
        consumer.close()


if __name__ == "__main__":
    asyncio.run(run())
