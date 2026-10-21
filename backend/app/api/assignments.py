import json
from pathlib import Path
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel

from app.assignments.compile import compile_assignment
from app.assignments.workspace import materialize_workspace
from app.db import SessionLocal
from app.ingest.snapshot import snapshot_dir
from app.jobs import create_job, run_job
from app.models import Assignment, Plan, Project
from app.schemas import AssignmentArtifact, LearningPlan

router = APIRouter(prefix="/api", tags=["assignments"])


def _run_compile_assignments_job(plan_id: str):
    db = SessionLocal()
    try:
        plan_row = db.query(Plan).filter(Plan.id == plan_id).first()
        if not plan_row:
            raise ValueError("Plan not found")
        plan = LearningPlan.model_validate_json(plan_row.json)
        snap = snapshot_dir(plan_row.project_id)

        artifacts = []
        for a_plan in plan.assignments:
            art = compile_assignment(plan_id=plan_id, plan_assignment=a_plan, snapshot=snap)
            artifacts.append(art.model_dump())
        return {"compiled": len(artifacts), "assignments": artifacts}
    finally:
        db.close()


@router.post("/plans/{plan_id}/assignments/generate")
def generate_assignments_endpoint(plan_id: str, background_tasks: BackgroundTasks):
    db = SessionLocal()
    try:
        plan_row = db.query(Plan).filter(Plan.id == plan_id).first()
        if not plan_row:
            raise HTTPException(status_code=404, detail="Plan not found")

        job = create_job("generate_assignments", db=db)
        background_tasks.add_task(run_job, job.id, _run_compile_assignments_job, plan_id)
        return {"job_id": job.id}
    finally:
        db.close()


@router.get("/assignments/{assignment_id}")
def get_assignment(assignment_id: str, view: str = Query("mentor")):
    db = SessionLocal()
    try:
        a_row = db.query(Assignment).filter(Assignment.id == assignment_id).first()
        if not a_row:
            raise HTTPException(status_code=404, detail="Assignment not found")

        art = AssignmentArtifact.model_validate_json(a_row.artifact_json)
        data = art.model_dump()

        if view == "learner":
            # Strip hidden tests and any reference notes from learner view
            data.pop("hidden_tests", None)

        data["published"] = a_row.published
        return data
    finally:
        db.close()


@router.patch("/assignments/{assignment_id}")
def update_assignment(assignment_id: str, artifact_data: AssignmentArtifact):
    db = SessionLocal()
    try:
        a_row = db.query(Assignment).filter(Assignment.id == assignment_id).first()
        if not a_row:
            raise HTTPException(status_code=404, detail="Assignment not found")
        a_row.artifact_json = artifact_data.model_dump_json()
        db.commit()
        return {"id": a_row.id, "artifact": artifact_data.model_dump()}
    finally:
        db.close()


@router.post("/assignments/{assignment_id}/publish")
def publish_assignment(assignment_id: str):
    db = SessionLocal()
    try:
        a_row = db.query(Assignment).filter(Assignment.id == assignment_id).first()
        if not a_row:
            raise HTTPException(status_code=404, detail="Assignment not found")
        a_row.published = True
        db.commit()
        return {"id": a_row.id, "published": True}
    finally:
        db.close()


@router.post("/assignments/{assignment_id}/workspace")
def create_workspace_endpoint(assignment_id: str):
    db = SessionLocal()
    try:
        a_row = db.query(Assignment).filter(Assignment.id == assignment_id).first()
        if not a_row:
            raise HTTPException(status_code=404, detail="Assignment not found")
        plan_row = db.query(Plan).filter(Plan.id == a_row.plan_id).first()
        if not plan_row:
            raise HTTPException(status_code=404, detail="Plan not found")
        proj_row = db.query(Project).filter(Project.id == plan_row.project_id).first()
        if not proj_row:
            raise HTTPException(status_code=404, detail="Project not found")

        art = AssignmentArtifact.model_validate_json(a_row.artifact_json)
        snap = Path(proj_row.snapshot_path)
        ws_id = materialize_workspace(
            project_id=plan_row.project_id,
            assignment=art,
            snapshot_path=snap,
        )
        return {"workspace_id": ws_id}
    finally:
        db.close()
