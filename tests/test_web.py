"""Test the web interface functionality."""

import pytest
from fastapi.testclient import TestClient

from example_cloud_distributed_quicksort.web import app, job_manager, JobStatus


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI app."""
    # Clear any existing jobs before each test
    job_manager.jobs.clear()
    # Force test mode for tests
    job_manager.test_mode = True
    return TestClient(app)


def test_home_page(client: TestClient) -> None:
    """Test that the home page loads correctly."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Distributed Quicksort" in response.text
    assert "Submit New Sorting Job" in response.text


def test_submit_job(client: TestClient) -> None:
    """Test job submission."""
    test_data = [64, 34, 25, 12, 22, 11, 90]
    response = client.post("/jobs", json={"data": test_data})

    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert "message" in data
    assert data["message"] == "Job submitted successfully"


def test_list_empty_jobs(client: TestClient) -> None:
    """Test listing jobs when there are none."""
    response = client.get("/jobs")
    assert response.status_code == 200
    assert response.json() == []


def test_job_creation_and_retrieval(client: TestClient) -> None:
    """Test creating a job and retrieving it."""
    test_data = [5, 2, 8, 1, 9]

    # Submit job
    response = client.post("/jobs", json={"data": test_data})
    assert response.status_code == 200
    job_id = response.json()["job_id"]

    # Get specific job
    response = client.get(f"/jobs/{job_id}")
    assert response.status_code == 200

    job = response.json()
    assert job["id"] == job_id
    assert job["data"] == test_data
    assert job["status"] in [JobStatus.PENDING, JobStatus.RUNNING, JobStatus.COMPLETED]


def test_job_not_found(client: TestClient) -> None:
    """Test retrieving a non-existent job."""
    response = client.get("/jobs/non-existent-id")
    assert response.status_code == 404
    assert "Job not found" in response.json()["detail"]


def test_empty_data_submission(client: TestClient) -> None:
    """Test submitting an empty data array."""
    response = client.post("/jobs", json={"data": []})
    assert response.status_code == 400
    assert "Data cannot be empty" in response.json()["detail"]


@pytest.mark.asyncio
async def test_job_execution() -> None:
    """Test that job execution works correctly."""
    # Clear any existing jobs
    job_manager.jobs.clear()

    test_data = [3, 1, 4, 1, 5]
    expected_result = [1, 1, 3, 4, 5]

    # Create a job
    job_id = job_manager.create_job(test_data)

    # Execute the job
    await job_manager.execute_job(job_id)

    # Check the result
    job = job_manager.get_job(job_id)
    assert job is not None
    assert job.status == JobStatus.COMPLETED
    assert job.result == expected_result
    assert job.error is None
    assert job.completed_at is not None
