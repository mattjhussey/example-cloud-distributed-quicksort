# Use the official Python 3.12 image as the base image
FROM python:3.12-slim AS base

# Set the working directory in the container
WORKDIR /app

# Copy the source code into the container
COPY . ./

# Install build dependencies
RUN pip install uv && uv sync

FROM base AS build

RUN uv build

FROM base AS test

RUN \
    uv run pytest && \
    uv run black --check . && \
    uv run ruff check && \
    uv run mypy .

FROM python:3.12-slim AS run

# Set the working directory in the container
WORKDIR /app

COPY --from=build /app/dist /app/dist

RUN pip install --no-cache-dir dist/*.whl

# Expose the port for the web server
EXPOSE 8000

# Set the default command to run the web server
CMD ["quicksort-web"]
