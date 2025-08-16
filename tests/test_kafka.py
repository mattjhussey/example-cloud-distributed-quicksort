"""Test Kafka integration components."""

import pytest
from unittest.mock import AsyncMock

from example_cloud_distributed_quicksort.kafka_utils import (
    KafkaConfig,
    JobEventProducer,
    JobStatusProducer,
    JobEventConsumer,
    JobStatusConsumer,
)
from example_cloud_distributed_quicksort.processor import JobProcessor


def test_kafka_config():
    """Test KafkaConfig with default values."""
    config = KafkaConfig()
    assert config.bootstrap_servers == "localhost:9092"
    assert config.job_topic == "quicksort-jobs"
    assert config.status_topic == "quicksort-status"


@pytest.mark.asyncio
async def test_job_event_producer():
    """Test JobEventProducer initialization."""
    producer = JobEventProducer()
    assert producer.config is not None
    assert producer.producer is None
    # Can't test actual Kafka operations without Kafka running


@pytest.mark.asyncio
async def test_job_status_producer():
    """Test JobStatusProducer initialization."""
    producer = JobStatusProducer()
    assert producer.config is not None
    assert producer.producer is None
    # Can't test actual Kafka operations without Kafka running


@pytest.mark.asyncio
async def test_job_event_consumer():
    """Test JobEventConsumer initialization."""
    consumer = JobEventConsumer()
    assert consumer.config is not None
    assert consumer.consumer is None
    # Can't test actual Kafka operations without Kafka running


@pytest.mark.asyncio
async def test_job_status_consumer():
    """Test JobStatusConsumer initialization."""
    consumer = JobStatusConsumer()
    assert consumer.config is not None
    assert consumer.consumer is None
    # Can't test actual Kafka operations without Kafka running


@pytest.mark.asyncio
async def test_job_processor():
    """Test JobProcessor initialization."""
    processor = JobProcessor()
    assert processor.config is not None
    assert processor.consumer is not None
    assert processor.status_producer is not None
    assert processor._running is False


@pytest.mark.asyncio
async def test_job_processor_process_single_job():
    """Test JobProcessor._process_single_job with mock event."""
    processor = JobProcessor()

    # Mock the status producer
    processor.status_producer = AsyncMock()

    # Test with valid job event
    job_event = {
        "job_id": "test-job-123",
        "data": [3, 1, 4, 1, 5],
        "event_type": "job_created",
    }

    await processor._process_single_job(job_event)

    # Verify status updates were called
    assert processor.status_producer.publish_status.call_count >= 2
    # First call should be for "running" status
    first_call = processor.status_producer.publish_status.call_args_list[0]
    assert first_call[0][1] == "running"

    # Last call should be for "completed" status with result
    last_call = processor.status_producer.publish_status.call_args_list[-1]
    assert last_call[0][1] == "completed"
    assert last_call[1]["result"] == [1, 1, 3, 4, 5]


@pytest.mark.asyncio
async def test_job_processor_invalid_event():
    """Test JobProcessor._process_single_job with invalid event."""
    processor = JobProcessor()

    # Mock the status producer
    processor.status_producer = AsyncMock()

    # Test with invalid job event (missing job_id)
    invalid_event = {"data": [3, 1, 4], "event_type": "job_created"}

    await processor._process_single_job(invalid_event)

    # Should not call status producer for invalid events
    processor.status_producer.publish_status.assert_not_called()


@pytest.mark.asyncio
async def test_job_processor_error_handling():
    """Test JobProcessor._process_single_job error handling."""
    processor = JobProcessor()

    # Mock the status producer
    processor.status_producer = AsyncMock()

    # Test with job that will cause processing error (valid data but force error)
    job_event = {
        "job_id": "error-job-123",
        "data": [1, 2, 3],  # Valid data
        "event_type": "job_created",
    }

    # Mock the quicksort function to raise an error
    import example_cloud_distributed_quicksort.processor
    import example_cloud_distributed_quicksort.main

    # Temporarily replace quicksort_distributed to simulate an error
    original_func = example_cloud_distributed_quicksort.main.quicksort_distributed

    async def mock_quicksort_error(data):
        raise ValueError("Simulated processing error")

    example_cloud_distributed_quicksort.main.quicksort_distributed = (
        mock_quicksort_error
    )

    try:
        await processor._process_single_job(job_event)

        # Should call status producer at least twice (running, then failed)
        assert processor.status_producer.publish_status.call_count >= 2

        # Last call should be for "failed" status
        last_call = processor.status_producer.publish_status.call_args_list[-1]
        assert last_call[0][1] == "failed"
        assert last_call[1]["error"] is not None
    finally:
        # Restore original function
        example_cloud_distributed_quicksort.main.quicksort_distributed = original_func
