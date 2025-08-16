# Use the official Python 3.12 image as the base image
FROM python:3.12-slim AS base

# Set the working directory in the container
WORKDIR /app

# Install build dependencies
RUN pip install --no-cache-dir uv==0.8.*

# Copy the source code into the container (using .dockerignore to filter)
COPY . ./

# Run UV to fetch dependencies
RUN uv sync

# Build the application
FROM base AS build

RUN uv build

# Test and linting stage (for CI pipelines, not included in production)
FROM base AS test

RUN \
    uv run pytest && \
    uv run black --check . && \
    uv run ruff check && \
    uv run mypy .

# Create a developer entry point
FROM base AS dev

FROM python:3.12-slim AS run

# Install dependencies
RUN apt update && apt install -y curl

# Run as non-root user
RUN adduser --disabled-password --gecos '' appuser

COPY --from=build /app/dist /app/dist

RUN chown -R appuser:appuser /app

USER appuser

# Set the working directory in the container
WORKDIR /app

# Ensure the PATH includes the directory for user-installed executables
ENV PATH="/home/appuser/.local/bin:$PATH"

RUN pip install --no-cache-dir dist/*.whl

# Check the health of the container
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000 || exit 1

# Expose the port for the web server
EXPOSE 8000

# Set the default command to run the web server
CMD ["quicksort-web"]
