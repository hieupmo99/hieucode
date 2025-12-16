import json
import os
from kafka import KafkaProducer

# Determine sensible defaults depending on runtime (local vs Docker)
# Updated: 2025-12-16 - Trigger build-deploy workflow
DOCKER_ENV = os.environ.get("DOCKER_ENV")
DEFAULT_BOOTSTRAP_LOCAL = "localhost:19092,localhost:29092,localhost:39092"
DEFAULT_BOOTSTRAP_DOCKER = "kafka-1:9092,kafka-2:9092,kafka-3:9092"

KAFKA_BOOTSTRAP = os.environ.get(
    "KAFKA_BOOTSTRAP",
    DEFAULT_BOOTSTRAP_DOCKER if DOCKER_ENV else DEFAULT_BOOTSTRAP_LOCAL,
)
TOPIC = os.environ.get("KAFKA_TOPIC", "vnexpress_topic")

_producer = None


def _get_producer() -> KafkaProducer:
    """
    Create a singleton KafkaProducer using env-configured bootstrap servers.
    """
    global _producer
    if _producer is None:
        _producer = KafkaProducer(
            bootstrap_servers=[
                s.strip() for s in KAFKA_BOOTSTRAP.split(",") if s.strip()
            ],
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        # Lightweight visibility to help debug routing
        print(
            "Kafka producer initialized -> bootstrap: "
            f"{KAFKA_BOOTSTRAP} | topic: {TOPIC}"
        )
    return _producer


def send_crawled_item(item: dict) -> None:
    """Send a JSON-serializable dict to the configured Kafka topic."""
    prod = _get_producer()
    prod.send(TOPIC, item)
    prod.flush()


def close_producer() -> None:
    global _producer
    if _producer is not None:
        try:
            _producer.flush()
            _producer.close()
        finally:
            _producer = None

