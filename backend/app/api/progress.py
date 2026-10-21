from fastapi import APIRouter, HTTPException

from app.db import SessionLocal
from app.models import Progress

router = APIRouter(prefix="/api", tags=["progress"])


@router.get("/progress")
def get_progress():
    db = SessionLocal()
    try:
        rows = db.query(Progress).all()
        return [
            {"assignment_id": r.assignment_id, "passed": r.passed} for r in rows
        ]
    finally:
        db.close()


@router.get("/progress/{assignment_id}")
def get_assignment_progress(assignment_id: str):
    db = SessionLocal()
    try:
        row = db.query(Progress).filter(Progress.assignment_id == assignment_id).first()
        if not row:
            return {"assignment_id": assignment_id, "passed": False}
        return {"assignment_id": assignment_id, "passed": row.passed}
    finally:
        db.close()