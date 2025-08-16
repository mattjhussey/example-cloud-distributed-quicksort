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

### Running with Docker Compose (Kafka-enabled distributed processing)

The fastest way to run the full distributed system with Kafka:

```bash
# Build and start all services (Kafka, Zookeeper, Web interface, and Processor)
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build

# Check the logs
docker-compose logs -f

# Stop all services
docker-compose down
```

Services will be available at:
- **Web Interface**: http://localhost:8000 - Submit and monitor sorting jobs
- **Kafka UI**: http://localhost:8080 - Monitor Kafka topics and messages (optional)

The system consists of:
- **quicksort-web**: Web interface that accepts job submissions and publishes them to Kafka
- **quicksort-processor**: Background service that consumes jobs from Kafka and processes them
- **kafka**: Message broker for job distribution
- **zookeeper**: Kafka coordination service

### Running the Application

You can run the application in several ways:

1. **Web Interface (Local development)** - Run without Kafka for development:
   ```bash
   # Set environment variable to disable Kafka
   export KAFKA_DISABLED=true
   
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

4. **Job Processor** - Run the Kafka-based job processor:
   ```bash
   # Requires Kafka to be running
   quicksort-processor
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
│       ├── web.py            # FastAPI web interface with Kafka integration
│       ├── processor.py      # Kafka job processor service (NEW)
│       └── kafka_utils.py    # Kafka producer/consumer utilities (NEW)
├── tests/
│   ├── __init__.py
│   ├── test_main.py
│   └── test_web.py
├── main.py                   # Entry point script
├── docker-compose.yml        # Docker Compose for full stack (NEW)
├── Dockerfile               # Application container
├── pyproject.toml           # Project configuration
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
3. **Kafka Integration**: Message-driven distributed processing with:
   - Job submission through Kafka topics
   - Separate processing services that can scale independently
   - Status updates propagated back through Kafka
   - Docker Compose setup for easy deployment

This serves as a foundation for building a true distributed version that can:

- Split sorting tasks across multiple Kubernetes pods
- Use message queues for inter-node communication (✅ **IMPLEMENTED with Kafka**)
- Handle fault tolerance and load balancing
- Monitor performance across the cluster

## Future Enhancements

- [x] Implement distributed sorting across multiple nodes (**PARTIALLY DONE**: Kafka-based job distribution)
- [ ] Add Kubernetes deployment configurations
- [x] Integrate with message queues (e.g., Redis, RabbitMQ) (**DONE**: Kafka integration)
- [ ] Add monitoring and metrics
- [ ] Implement fault tolerance and recovery
- [ ] Add performance benchmarking

## License

This project is open source and available under the [MIT License](LICENSE).
