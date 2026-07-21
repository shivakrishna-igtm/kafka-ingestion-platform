"""Kafka topic creation. No-op with a log line when no broker is configured,
so the registry works standalone; with KAFKA_BOOTSTRAP set (docker compose),
registration actually creates the topic on the broker."""
import logging

from .config import settings

log = logging.getLogger("kafka")


def create_topic(name: str, partitions: int = 3) -> bool:
    if not settings.kafka_bootstrap:
        log.info("kafka: no broker configured, registry-only mode for topic=%s", name)
        return False
    try:
        from confluent_kafka.admin import AdminClient, NewTopic  # noqa: PLC0415
        admin = AdminClient({"bootstrap.servers": settings.kafka_bootstrap})
        futures = admin.create_topics([NewTopic(name, num_partitions=partitions)])
        futures[name].result(timeout=10)
        log.info("kafka: created topic=%s partitions=%d", name, partitions)
        return True
    except Exception as e:  # noqa: BLE001
        log.warning("kafka: could not create topic=%s (%s)", name, e)
        return False
