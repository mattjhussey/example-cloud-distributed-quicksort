# Example Cloud Distributed Quicksort

An example distributed quicksort implementation for learning Kubernetes and cloud computing concepts.

## Overview

This project demonstrates a distributed quicksort algorithm designed to run across multiple nodes in a Kubernetes cluster. It's built as a learning exercise to explore:

- Distributed computing patterns
- Kubernetes orchestration
- Asynchronous Python programming
- Cloud-native application development

## Prerequisites

- Python 3.12 or later
- [uv](https://github.com/astral-sh/uv) package manager

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/mattjhussey/example-cloud-distributed-quicksort.git
   cd example-cloud-distributed-quicksort
   ```

2. Install the project and its dependencies using uv:
   ```bash
   uv sync
   ```

## Usage

### Running the Application

You can run the application in several ways:

1. Using the main script:
   ```bash
   uv run main.py
   ```

2. Using the installed CLI command:
   ```bash
   uv run quicksort
   ```

### Development

To work on the project with development dependencies:

```bash
# Install with dev dependencies
uv sync --extra dev

# Run tests
uv run pytest

# Run linting
uv run ruff check .

# Format code
uv run black .

# Type checking
uv run mypy .
```

## Project Structure

```
.
├── src/
│   └── example_cloud_distributed_quicksort/
│       ├── __init__.py
│       └── main.py
├── tests/
│   ├── __init__.py
│   └── test_main.py
├── main.py              # Entry point script
├── pyproject.toml       # Project configuration
└── README.md
```

## Current Implementation

The current implementation provides a basic quicksort algorithm with structured logging and async support. This serves as a foundation for building a true distributed version that can:

- Split sorting tasks across multiple Kubernetes pods
- Use message queues for inter-node communication
- Handle fault tolerance and load balancing
- Monitor performance across the cluster

## Future Enhancements

- [ ] Implement distributed sorting across multiple nodes
- [ ] Add Kubernetes deployment configurations
- [ ] Integrate with message queues (e.g., Redis, RabbitMQ)
- [ ] Add monitoring and metrics
- [ ] Implement fault tolerance and recovery
- [ ] Add performance benchmarking

## License

This project is open source and available under the [MIT License](LICENSE).
