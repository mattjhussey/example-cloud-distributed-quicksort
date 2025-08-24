"""Kafka utilities for job processing."""

import json
import logging
import os
from typing import Any, List, Optional

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer  # type: ignore


class KafkaConfig:
    """Kafka configuration settings."""

    def __init__(self) -> None:
        self.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        self.job_topic = os.getenv("KAFKA_JOB_TOPIC", "quicksort-jobs")
        self.status_topic = os.getenv("KAFKA_STATUS_TOPIC", "quicksort-status")


class JobEventProducer:
    """Kafka producer for job events."""

    def __init__(self, config: Optional[KafkaConfig] = None) -> None:
        self.config = config or KafkaConfig()
        self.producer: Optional[AIOKafkaProducer] = None
        self.logger = logging.getLogger(__name__)

    async def start(self) -> None:
        """Start the Kafka producer."""
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.config.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        await self.producer.start()
        self.logger.info(
            f"Started Kafka producer connected to {self.config.bootstrap_servers}"
        )

    async def stop(self) -> None:
        """Stop the Kafka producer."""
        if self.producer:
            await self.producer.stop()
            self.logger.info("Stopped Kafka producer")

    async def publish_job(self, job_id: str, data: List[int]) -> None:
        """Publish a new job to the jobs topic."""
        if not self.producer:
            raise RuntimeError("Producer not started")

        job_event = {"job_id": job_id, "data": data, "event_type": "job_created"}

        await self.producer.send(self.config.job_topic, job_event)
        self.logger.info(f"Published job {job_id} to topic {self.config.job_topic}")


class JobStatusProducer:
    """Kafka producer for job status updates."""

    def __init__(self, config: Optional[KafkaConfig] = None) -> None:
        self.config = config or KafkaConfig()
        self.producer: Optional[AIOKafkaProducer] = None
        self.logger = logging.getLogger(__name__)

    async def start(self) -> None:
        """Start the Kafka producer."""
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.config.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        await self.producer.start()
        self.logger.info(
            f"Started Kafka status producer connected to {self.config.bootstrap_servers}"
        )

    async def stop(self) -> None:
        """Stop the Kafka producer."""
        if self.producer:
            await self.producer.stop()
            self.logger.info("Stopped Kafka status producer")

    async def publish_status(
        self,
        job_id: str,
        status: str,
        result: Optional[List[int]] = None,
        error: Optional[str] = None,
    ) -> None:
        """Publish job status update."""
        if not self.producer:
            raise RuntimeError("Producer not started")

        status_event = {
            "job_id": job_id,
            "status": status,
            "result": result,
            "error": error,
            "event_type": "status_update",
        }

        await self.producer.send(self.config.status_topic, status_event)
        self.logger.info(f"Published status update for job {job_id}: {status}")


class JobEventConsumer:
    """Kafka consumer for job events."""

    def __init__(self, config: Optional[KafkaConfig] = None) -> None:
        self.config = config or KafkaConfig()
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.logger = logging.getLogger(__name__)

    async def start(self) -> None:
        """Start the Kafka consumer."""
        self.consumer = AIOKafkaConsumer(
            self.config.job_topic,
            bootstrap_servers=self.config.bootstrap_servers,
            group_id="quicksort-processors",
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        )
        await self.consumer.start()
        self.logger.info(f"Started Kafka consumer for topic {self.config.job_topic}")

    async def stop(self) -> None:
        """Stop the Kafka consumer."""
        if self.consumer:
            await self.consumer.stop()
            self.logger.info("Stopped Kafka consumer")

    async def consume_jobs(self) -> Any:
        """Consume job events from Kafka."""
        if not self.consumer:
            raise RuntimeError("Consumer not started")

        async for message in self.consumer:
            yield message.value


class JobStatusConsumer:
    """Kafka consumer for job status updates."""

    def __init__(self, config: Optional[KafkaConfig] = None) -> None:
        self.config = config or KafkaConfig()
        self.consumer: Optional[AIOKafkaConsumer] = None
        self.logger = logging.getLogger(__name__)

    async def start(self) -> None:
        """Start the Kafka consumer."""
        self.consumer = AIOKafkaConsumer(
            self.config.status_topic,
            bootstrap_servers=self.config.bootstrap_servers,
            group_id="quicksort-web",
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        )
        await self.consumer.start()
        self.logger.info(
            f"Started Kafka status consumer for topic {self.config.status_topic}"
        )

    async def stop(self) -> None:
        """Stop the Kafka consumer."""
        if self.consumer:
            await self.consumer.stop()
            self.logger.info("Stopped Kafka status consumer")

    async def consume_status(self) -> Any:
        """Consume status events from Kafka."""
        if not self.consumer:
            raise RuntimeError("Consumer not started")

        async for message in self.consumer:
            yield message.value
