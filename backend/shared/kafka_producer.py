import os
import json
import logging
from confluent_kafka import Producer

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

log = logging.getLogger("kafka_producer")

_producer: Producer | None = None


def get_producer() -> Producer:
    global _producer
    if _producer is None:
        _producer = Producer({
            "bootstrap.servers": KAFKA_BOOTSTRAP_SERVERS,
            "socket.timeout.ms": 3000,
            "message.timeout.ms": 3000,
        })
    return _producer


def publish(topic: str, payload: dict, key: str | None = None) -> None:
    try:
        producer = get_producer()
        producer.produce(
            topic,
            key=key.encode("utf-8") if key else None,
            value=json.dumps(payload).encode("utf-8"),
        )
        producer.poll(0)
    except Exception as exc:
        # Kafka unavailable — log and continue; do not crash the API request
        log.warning("Kafka publish failed (topic=%s): %s", topic, exc)
