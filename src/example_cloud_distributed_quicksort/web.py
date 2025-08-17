"""FastAPI web interface for the distributed quicksort application."""

import asyncio
import logging
import os
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from .kafka_utils import JobEventProducer, JobStatusConsumer, KafkaConfig


class JobStatus(str, Enum):
    """Job status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Job(BaseModel):
    """Job data model."""

    id: str
    data: List[int]
    status: JobStatus
    result: Optional[List[int]] = None
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


class JobSubmission(BaseModel):
    """Job submission request model."""

    data: List[int]


class JobManager:
    """Kafka-enabled job manager."""

    def __init__(
        self, config: Optional[KafkaConfig] = None, test_mode: bool = False
    ) -> None:
        self.jobs: Dict[str, Job] = {}
        self.logger = logging.getLogger(__name__)
        self.config = config or KafkaConfig()
        self.test_mode = test_mode
        self.job_producer: Optional[JobEventProducer] = None
        self.status_consumer: Optional[JobStatusConsumer] = None
        self._status_task: Optional[asyncio.Task[None]] = None

    async def start(self) -> None:
        """Start Kafka producers and consumers."""
        if self.test_mode:
            self.logger.info("JobManager started in test mode (no Kafka)")
            return

        self.job_producer = JobEventProducer(self.config)
        await self.job_producer.start()

        self.status_consumer = JobStatusConsumer(self.config)
        await self.status_consumer.start()

        # Start background task to consume status updates
        self._status_task = asyncio.create_task(self._consume_status_updates())
        self.logger.info("JobManager started with Kafka integration")

    async def stop(self) -> None:
        """Stop Kafka producers and consumers."""
        if self.test_mode:
            self.logger.info("JobManager stopped from test mode")
            return

        if self._status_task:
            self._status_task.cancel()
            try:
                await self._status_task
            except asyncio.CancelledError:
                pass

        if self.job_producer:
            await self.job_producer.stop()

        if self.status_consumer:
            await self.status_consumer.stop()

        self.logger.info("JobManager stopped")

    async def _consume_status_updates(self) -> None:
        """Background task to consume job status updates from Kafka."""
        try:
            if self.status_consumer is not None:
                async for status_event in self.status_consumer.consume_status():
                    await self._handle_status_update(status_event)
        except asyncio.CancelledError:
            self.logger.info("Status consumer task cancelled")
        except Exception as e:
            self.logger.error(f"Error in status consumer: {e}")

    async def _handle_status_update(self, status_event: Dict[str, Any]) -> None:
        """Handle a job status update event."""
        job_id = status_event.get("job_id")
        status = status_event.get("status")
        result = status_event.get("result")
        error = status_event.get("error")

        if not job_id or not status:
            self.logger.error(f"Invalid status event: {status_event}")
            return

        job = self.jobs.get(job_id)
        if not job:
            self.logger.warning(f"Received status update for unknown job {job_id}")
            return

        # Update job status
        job.status = JobStatus(status)

        if result is not None:
            job.result = result

        if error:
            job.error = error

        if status in ["completed", "failed"]:
            job.completed_at = datetime.now()

        self.logger.info(f"Updated job {job_id} status to {status}")

    def create_job(self, data: List[int]) -> str:
        """Create a new job and return its ID."""
        job_id = str(uuid.uuid4())
        job = Job(
            id=job_id, data=data, status=JobStatus.PENDING, created_at=datetime.now()
        )
        self.jobs[job_id] = job
        self.logger.info(f"Created job {job_id} with {len(data)} elements")
        return job_id

    async def submit_job(self, job_id: str, data: List[int]) -> None:
        """Submit a job to Kafka for processing."""
        if self.test_mode:
            # In test mode, immediately mark as completed with sorted result
            job = self.jobs.get(job_id)
            if job:
                # Import here to avoid circular import
                from .main import quicksort_distributed

                job.status = JobStatus.RUNNING
                try:
                    job.result = await quicksort_distributed(data)
                    job.status = JobStatus.COMPLETED
                    job.completed_at = datetime.now()
                except Exception as e:
                    job.status = JobStatus.FAILED
                    job.error = str(e)
                    job.completed_at = datetime.now()
            return

        if not self.job_producer:
            raise RuntimeError("JobManager not started")

        await self.job_producer.publish_job(job_id, data)
        self.logger.info(f"Submitted job {job_id} to Kafka")

    def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID."""
        return self.jobs.get(job_id)

    def list_jobs(self) -> List[Job]:
        """List all jobs."""
        return list(self.jobs.values())

    # Keep this method for backward compatibility with tests
    async def execute_job(self, job_id: str) -> None:
        """Execute a job asynchronously (for backward compatibility with tests)."""
        job = self.jobs.get(job_id)
        if not job:
            return

        try:
            job.status = JobStatus.RUNNING
            self.logger.info(f"Starting execution of job {job_id}")

            # Import here to avoid circular import
            from .main import quicksort_distributed

            result = await quicksort_distributed(job.data)

            job.result = result
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now()

            self.logger.info(f"Completed job {job_id} successfully")

        except Exception as e:
            job.status = JobStatus.FAILED
            job.error = str(e)
            job.completed_at = datetime.now()

            self.logger.error(f"Job {job_id} failed: {e}")


# Global job manager instance - check environment for test mode
_test_mode = os.getenv("KAFKA_DISABLED", "false").lower() == "true"
job_manager = JobManager(test_mode=_test_mode)

# FastAPI application
app = FastAPI(
    title="Distributed Quicksort API",
    description="A web interface for submitting and monitoring distributed quicksort jobs",
    version="0.1.0",
)


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize Kafka connections on startup."""
    await job_manager.start()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Clean up Kafka connections on shutdown."""
    await job_manager.stop()


@app.get("/", response_class=HTMLResponse)
async def root() -> HTMLResponse:
    """Main web interface."""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Distributed Quicksort</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }
            .container { margin: 20px 0; }
            .job-form { background: #f5f5f5; padding: 20px; border-radius: 8px; }
            .job-list { background: #fff; border: 1px solid #ddd; border-radius: 8px; padding: 20px; }
            .job-item { border-bottom: 1px solid #eee; padding: 10px 0; }
            .job-item:last-child { border-bottom: none; }
            .status-pending { color: #666; }
            .status-running { color: #007bff; }
            .status-completed { color: #28a745; }
            .status-failed { color: #dc3545; }
            input[type="text"] { width: 400px; padding: 8px; margin: 5px; }
            button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background: #0056b3; }
            .refresh-btn { background: #6c757d; margin-left: 10px; }
            .refresh-btn:hover { background: #545b62; }
        </style>
    </head>
    <body>
        <h1>Distributed Quicksort</h1>
        
        <div class="container">
            <div class="job-form">
                <h2>Submit New Sorting Job</h2>
                <form id="jobForm">
                    <label for="data">Enter numbers to sort (comma-separated):</label><br>
                    <input type="text" id="data" name="data" placeholder="64,34,25,12,22,11,90" required>
                    <button type="submit">Submit Job</button>
                </form>
            </div>
        </div>
        
        <div class="container">
            <div class="job-list">
                <h2>Jobs 
                    <button class="refresh-btn" onclick="loadJobs()">Refresh</button>
                </h2>
                <div id="jobsList">Loading jobs...</div>
            </div>
        </div>
        
        <script>
            // Submit new job
            document.getElementById('jobForm').addEventListener('submit', async function(e) {
                e.preventDefault();
                
                const dataInput = document.getElementById('data');
                const dataStr = dataInput.value.trim();
                
                if (!dataStr) {
                    alert('Please enter some numbers to sort');
                    return;
                }
                
                try {
                    const data = dataStr.split(',').map(s => parseInt(s.trim())).filter(n => !isNaN(n));
                    
                    if (data.length === 0) {
                        alert('Please enter valid numbers separated by commas');
                        return;
                    }
                    
                    const response = await fetch('/jobs', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({data: data})
                    });
                    
                    if (response.ok) {
                        const result = await response.json();
                        alert('Job submitted successfully! Job ID: ' + result.job_id);
                        dataInput.value = '';
                        loadJobs();
                    } else {
                        throw new Error('Failed to submit job');
                    }
                } catch (error) {
                    alert('Error submitting job: ' + error.message);
                }
            });
            
            // Load and display jobs
            async function loadJobs() {
                try {
                    const response = await fetch('/jobs');
                    const jobs = await response.json();
                    
                    const jobsList = document.getElementById('jobsList');
                    
                    if (jobs.length === 0) {
                        jobsList.innerHTML = '<p>No jobs found.</p>';
                        return;
                    }
                    
                    let html = '';
                    jobs.forEach(job => {
                        const statusClass = 'status-' + job.status;
                        const createdAt = new Date(job.created_at).toLocaleString();
                        const completedAt = job.completed_at ? new Date(job.completed_at).toLocaleString() : 'N/A';
                        
                        html += `
                            <div class="job-item">
                                <strong>Job ID:</strong> ${job.id}<br>
                                <strong>Status:</strong> <span class="${statusClass}">${job.status.toUpperCase()}</span><br>
                                <strong>Input Data:</strong> [${job.data.join(', ')}]<br>
                                ${job.result ? `<strong>Sorted Result:</strong> [${job.result.join(', ')}]<br>` : ''}
                                ${job.error ? `<strong>Error:</strong> ${job.error}<br>` : ''}
                                <strong>Created:</strong> ${createdAt}<br>
                                <strong>Completed:</strong> ${completedAt}
                            </div>
                        `;
                    });
                    
                    jobsList.innerHTML = html;
                } catch (error) {
                    document.getElementById('jobsList').innerHTML = '<p>Error loading jobs: ' + error.message + '</p>';
                }
            }
            
            // Load jobs on page load
            loadJobs();
            
            // Auto-refresh jobs every 2 seconds
            setInterval(loadJobs, 2000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.post("/jobs")
async def submit_job(job_submission: JobSubmission) -> Dict[str, str]:
    """Submit a new sorting job."""
    if not job_submission.data:
        raise HTTPException(status_code=400, detail="Data cannot be empty")

    job_id = job_manager.create_job(job_submission.data)

    # Submit job to Kafka for processing
    await job_manager.submit_job(job_id, job_submission.data)

    return {"job_id": job_id, "message": "Job submitted successfully"}


@app.get("/jobs/{job_id}")
async def get_job(job_id: str) -> Job:
    """Get job status and results by ID."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return job


@app.get("/jobs")
async def list_jobs() -> List[Job]:
    """List all jobs."""
    jobs = job_manager.list_jobs()
    # Sort by creation time, newest first
    jobs.sort(key=lambda j: j.created_at, reverse=True)
    return jobs


def start_web_server(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Start the FastAPI web server."""
    import uvicorn

    uvicorn.run(app, host=host, port=port)


def web_main() -> None:
    """Web server CLI entry point."""
    import logging
    from .main import setup_logging

    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Distributed Quicksort Web Server")

    start_web_server()


if __name__ == "__main__":
    web_main()
