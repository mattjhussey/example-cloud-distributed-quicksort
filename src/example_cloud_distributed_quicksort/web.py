"""FastAPI web interface for the distributed quicksort application."""

import asyncio
import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from .main import quicksort_distributed


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
    """Simple in-memory job manager."""

    def __init__(self) -> None:
        self.jobs: Dict[str, Job] = {}
        self.logger = logging.getLogger(__name__)

    def create_job(self, data: List[int]) -> str:
        """Create a new job and return its ID."""
        job_id = str(uuid.uuid4())
        job = Job(
            id=job_id, data=data, status=JobStatus.PENDING, created_at=datetime.now()
        )
        self.jobs[job_id] = job
        self.logger.info(f"Created job {job_id} with {len(data)} elements")
        return job_id

    def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by ID."""
        return self.jobs.get(job_id)

    def list_jobs(self) -> List[Job]:
        """List all jobs."""
        return list(self.jobs.values())

    async def execute_job(self, job_id: str) -> None:
        """Execute a job asynchronously."""
        job = self.jobs.get(job_id)
        if not job:
            return

        try:
            job.status = JobStatus.RUNNING
            self.logger.info(f"Starting execution of job {job_id}")

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


# Global job manager instance
job_manager = JobManager()

# FastAPI application
app = FastAPI(
    title="Distributed Quicksort API",
    description="A web interface for submitting and monitoring distributed quicksort jobs",
    version="0.1.0",
)


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

    # Execute the job asynchronously
    asyncio.create_task(job_manager.execute_job(job_id))

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
