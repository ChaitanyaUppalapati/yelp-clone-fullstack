import os
import json
from confluent_kafka import Producer

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

_producer: Producer | None = None


def get_producer() -> Producer:
    global _producer
    if _producer is None:
        _producer = Producer({"bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS})
    return _producer


def publish(topic: str, payload: dict, key: str | None = None) -> None:
    producer = get_producer()
    producer.produce(
        topic,
        key=key.encode("utf-8") if key else None,
        value=json.dumps(payload).encode("utf-8"),
    )
    producer.poll(0)
