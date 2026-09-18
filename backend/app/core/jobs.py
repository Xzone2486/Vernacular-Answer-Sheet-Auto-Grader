"""
Lightweight in-process background job tracker.

Provides a simple job lifecycle (pending → running → completed/failed) with
progress tracking.  Jobs are stored in an in-memory dict — they are NOT
persisted across process restarts.

Extension Point — Swapping in Celery / RQ
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
To swap in a production task queue:
  1. Replace ``JobTracker`` internals with Celery task dispatch.
  2. ``create_job()`` → ``task.delay()`` returning the Celery task ID.
  3. ``get_job()`` → ``AsyncResult(job_id)`` status check.
  4. The API routes (``/jobs/{id}``) remain unchanged.
"""

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class JobInfo(BaseModel):
    id: str
    status: JobStatus
    description: str
    created_at: datetime
    updated_at: datetime
    processed: int = 0
    total: int = 0
    error: Optional[str] = None
    result: Optional[Any] = None


class JobTracker:
    """Singleton job tracker.  Thread-safe for asyncio (single event loop)."""

    _instance: Optional["JobTracker"] = None
    _jobs: Dict[str, JobInfo]

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._jobs = {}
        return cls._instance

    def create_job(self, description: str, total: int = 0) -> str:
        job_id = uuid.uuid4().hex[:12]
        now = datetime.now(timezone.utc)
        self._jobs[job_id] = JobInfo(
            id=job_id,
            status=JobStatus.PENDING,
            description=description,
            created_at=now,
            updated_at=now,
            total=total,
        )
        logger.info("Created job %s: %s (total=%d)", job_id, description, total)
        return job_id

    def update_progress(self, job_id: str, processed: int, status: Optional[JobStatus] = None):
        job = self._jobs.get(job_id)
        if not job:
            return
        job.processed = processed
        job.updated_at = datetime.now(timezone.utc)
        if status:
            job.status = status

    def complete_job(self, job_id: str, result: Any = None):
        job = self._jobs.get(job_id)
        if not job:
            return
        job.status = JobStatus.COMPLETED
        job.processed = job.total
        job.result = result
        job.updated_at = datetime.now(timezone.utc)
        logger.info("Job %s completed.", job_id)

    def fail_job(self, job_id: str, error: str):
        job = self._jobs.get(job_id)
        if not job:
            return
        job.status = JobStatus.FAILED
        job.error = error
        job.updated_at = datetime.now(timezone.utc)
        logger.error("Job %s failed: %s", job_id, error)

    def get_job(self, job_id: str) -> Optional[JobInfo]:
        return self._jobs.get(job_id)

    def list_jobs(self, limit: int = 20) -> List[JobInfo]:
        return sorted(self._jobs.values(), key=lambda j: j.created_at, reverse=True)[:limit]

    def start_job(self, job_id: str):
        job = self._jobs.get(job_id)
        if job:
            job.status = JobStatus.RUNNING
            job.updated_at = datetime.now(timezone.utc)


# Module-level singleton
job_tracker = JobTracker()
