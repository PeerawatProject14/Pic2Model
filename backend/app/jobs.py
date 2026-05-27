"""In-memory job registry + a single-worker background queue.

Single worker on purpose: ML models are VRAM-hungry, so we run one job at a
time and load/unload model backends sequentially. Good enough for single-user.
"""
from __future__ import annotations

import threading
import uuid
from datetime import datetime, timezone
from queue import Queue
from typing import Callable, Optional

from .schemas import Job, JobKind


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class JobManager:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._queue: "Queue[tuple[str, Callable[[JobHandle], None]]]" = Queue()
        self._lock = threading.Lock()
        self._worker = threading.Thread(target=self._run, daemon=True)
        self._worker.start()

    def submit(self, kind: JobKind, fn: "Callable[[JobHandle], None]") -> Job:
        job_id = uuid.uuid4().hex[:12]
        now = _utcnow()
        job = Job(id=job_id, kind=kind, status="queued", created_at=now, updated_at=now)
        with self._lock:
            self._jobs[job_id] = job
        self._queue.put((job_id, fn))
        return job

    def get(self, job_id: str) -> Optional[Job]:
        with self._lock:
            return self._jobs.get(job_id)

    def list(self) -> list[Job]:
        with self._lock:
            return sorted(self._jobs.values(), key=lambda j: j.created_at, reverse=True)

    def _update(self, job_id: str, **fields) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return
            for k, v in fields.items():
                setattr(job, k, v)
            job.updated_at = _utcnow()

    def _run(self) -> None:
        while True:
            job_id, fn = self._queue.get()
            self._update(job_id, status="running", progress=0.05)
            handle = JobHandle(self, job_id)
            try:
                fn(handle)
                # fn is responsible for setting result_id; mark done if not errored.
                job = self.get(job_id)
                if job and job.status != "error":
                    self._update(job_id, status="done", progress=1.0)
            except Exception as exc:  # noqa: BLE001 - surface any failure to the UI
                self._update(job_id, status="error", error=str(exc), message="failed")
            finally:
                self._queue.task_done()


class JobHandle:
    """Passed to job functions so they can report progress + the final result."""

    def __init__(self, manager: JobManager, job_id: str):
        self._m = manager
        self.id = job_id

    def progress(self, value: float, message: str = "") -> None:
        self._m._update(self.id, progress=value, message=message)

    def done(self, result_id: str) -> None:
        self._m._update(self.id, result_id=result_id, status="done", progress=1.0)


# Global singleton
job_manager = JobManager()
