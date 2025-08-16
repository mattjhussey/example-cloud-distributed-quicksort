"""Main module for the example cloud distributed quicksort package."""

import asyncio
import logging
from kafka import KafkaConsumer
import json


def setup_logging() -> None:
    """Set up basic logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


async def quicksort_distributed(data: list[int]) -> list[int]:
    """
    Placeholder for distributed quicksort implementation.

    This will be expanded to implement a distributed quicksort algorithm
    that can run across multiple nodes in a Kubernetes cluster.

    Args:
        data: List of integers to sort

    Returns:
        Sorted list of integers
    """
    # For now, just use Python's built-in sort as a placeholder
    logger = logging.getLogger(__name__)
    logger.info(f"Starting distributed quicksort with {len(data)} elements")

    # Simple quicksort implementation for demo
    if len(data) <= 1:
        return data

    pivot = data[len(data) // 2]
    left = [x for x in data if x < pivot]
    middle = [x for x in data if x == pivot]
    right = [x for x in data if x > pivot]

    # In a real distributed implementation, left and right would be processed
    # on different nodes/pods
    sorted_left = await quicksort_distributed(left)
    sorted_right = await quicksort_distributed(right)

    result = sorted_left + middle + sorted_right
    logger.info(f"Completed distributed quicksort with {len(result)} elements")
    return result


async def process_kafka_jobs() -> None:
    """Consume and process jobs from Kafka."""
    consumer = KafkaConsumer(
        "quicksort-jobs",
        bootstrap_servers="kafka:9092",  # Use the Kafka container hostname
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    )
    logger = logging.getLogger(__name__)

    for message in consumer:
        job = message.value
        job_id = job["job_id"]
        data = job["data"]
        logger.info(f"Received job {job_id} with {len(data)} elements from Kafka")

        # Process the job
        sorted_data = await quicksort_distributed(data)
        logger.info(f"Job {job_id} completed. Result: {sorted_data}")


async def main() -> None:
    """Main application entry point."""
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Starting example cloud distributed quicksort application")

    # Start Kafka job processing
    await process_kafka_jobs()


def cli_main() -> None:
    """CLI entry point that handles asyncio properly."""
    asyncio.run(main())


if __name__ == "__main__":
    cli_main()
