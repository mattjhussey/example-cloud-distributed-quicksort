"""Job processing service that consumes jobs from Kafka."""

import asyncio
import logging
from typing import Any, Dict, Optional

from .kafka_utils import JobEventConsumer, JobStatusProducer, KafkaConfig
from .main import quicksort_distributed, setup_logging


class JobProcessor:
    """Processes jobs consumed from Kafka."""

    def __init__(self, config: Optional[KafkaConfig] = None) -> None:
        self.config = config or KafkaConfig()
        self.consumer = JobEventConsumer(self.config)
        self.status_producer = JobStatusProducer(self.config)
        self.logger = logging.getLogger(__name__)
        self._running = False

    async def start(self) -> None:
        """Start the job processor."""
        await self.consumer.start()
        await self.status_producer.start()
        self._running = True
        self.logger.info("Job processor started")

    async def stop(self) -> None:
        """Stop the job processor."""
        self._running = False
        await self.consumer.stop()
        await self.status_producer.stop()
        self.logger.info("Job processor stopped")

    async def process_jobs(self) -> None:
        """Main processing loop."""
        self.logger.info("Starting job processing loop")

        async for job_event in self.consumer.consume_jobs():
            if not self._running:
                break

            await self._process_single_job(job_event)

    async def _process_single_job(self, job_event: Dict[str, Any]) -> None:
        """Process a single job."""
        job_id = job_event.get("job_id")
        data = job_event.get("data", [])

        if not job_id or not data:
            self.logger.error(f"Invalid job event: {job_event}")
            return

        self.logger.info(f"Processing job {job_id} with {len(data)} elements")

        try:
            # Update status to running
            await self.status_producer.publish_status(job_id, "running")

            # Process the job
            result = await quicksort_distributed(data)

            # Update status to completed with result
            await self.status_producer.publish_status(
                job_id, "completed", result=result
            )

            self.logger.info(f"Completed job {job_id} successfully")

        except Exception as e:
            # Update status to failed with error
            await self.status_producer.publish_status(job_id, "failed", error=str(e))
            self.logger.error(f"Job {job_id} failed: {e}")


async def main() -> None:
    """Main entry point for the job processor."""
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Starting Distributed Quicksort Job Processor")

    processor = JobProcessor()

    try:
        await processor.start()
        await processor.process_jobs()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Processor error: {e}")
        raise
    finally:
        await processor.stop()


def processor_main() -> None:
    """CLI entry point for the job processor."""
    asyncio.run(main())


if __name__ == "__main__":
    processor_main()
