"""Main entry point for the example cloud distributed quicksort application."""

import asyncio
import structlog


def setup_logging():
    """Set up structured logging."""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
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
    logger = structlog.get_logger()
    logger.info("Starting distributed quicksort", data_size=len(data))

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
    logger.info("Completed distributed quicksort", result_size=len(result))
    return result


async def main() -> None:
    """Main application entry point."""
    setup_logging()
    logger = structlog.get_logger()

    logger.info("Starting example cloud distributed quicksort application")

    # Example data to sort
    test_data = [64, 34, 25, 12, 22, 11, 90]
    logger.info("Input data", data=test_data)

    sorted_data = await quicksort_distributed(test_data)
    logger.info("Sorted data", data=sorted_data)

    print(f"Original: {test_data}")
    print(f"Sorted:   {sorted_data}")


if __name__ == "__main__":
    asyncio.run(main())
