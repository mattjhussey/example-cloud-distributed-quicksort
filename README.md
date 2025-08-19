# Example Kafka

An example project for learning Kafka.

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

1. **Web Interface (NEW)** - Run the FastAPI web server:
   ```bash
   # Using PYTHONPATH
   PYTHONPATH=src python -m example_cloud_distributed_quicksort.web
   
   # Or using the installed CLI command (if package is installed)
   quicksort-web
   ```
   
   Then open your web browser to http://localhost:8000 to:
   - Submit new sorting jobs through a web form
   - View job results and status
   - Monitor currently running jobs
   - Browse job history

2. **Command Line** - Using the main script:
   ```bash
   PYTHONPATH=src python -c "from src.example_cloud_distributed_quicksort.main import cli_main; cli_main()"
   ```

3. **Using the installed CLI command** (if package is installed):
   ```bash
   quicksort
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
│       ├── main.py           # Core quicksort implementation and CLI
│       └── web.py            # FastAPI web interface (NEW)
├── tests/
│   ├── __init__.py
│   └── test_main.py
├── main.py              # Entry point script
├── pyproject.toml       # Project configuration
└── README.md
```

## Current Implementation

The current implementation provides:

1. **Core Algorithm**: A basic quicksort algorithm with structured logging and async support
2. **Web Interface**: A FastAPI-based web frontend that allows users to:
   - Submit sorting jobs through a web browser
   - View real-time job status and results
   - Monitor job history with timestamps
   - Access the service through a REST API

This serves as a foundation for building a true distributed version that can:

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
