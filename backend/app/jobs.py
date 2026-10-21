import json
import logging
from datetime import datetime, timezone
from typing import Any, Callable
from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.models import Job

logger = logging.getLogger(__name__)


def create_job(kind: str, db: Session | None = None) -> Job:
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
    try:
        job = Job(kind=kind, status="queued")
        db.add(job)
        db.commit()
        db.refresh(job)
        return job
    finally:
        if close_db:
            db.close()


def run_job(job_id: str, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found")
            return None

        job.status = "running"
        job.updated_at = datetime.now(timezone.utc)
        db.commit()

        try:
            result = fn(*args, **kwargs)
            job.status = "done"
            if isinstance(result, str):
                job.result_json = result
            elif hasattr(result, "model_dump_json"):
                job.result_json = result.model_dump_json()
            elif isinstance(result, (dict, list)):
                job.result_json = json.dumps(result)
            else:
                job.result_json = json.dumps({"result": str(result)})
            job.updated_at = datetime.now(timezone.utc)
            db.commit()
            return result
        except Exception as e:
            logger.exception(f"Job {job_id} failed: {e}")
            job.status = "error"
            job.error = str(e)
            job.updated_at = datetime.now(timezone.utc)
            db.commit()
            raise
    finally:
        db.close()
