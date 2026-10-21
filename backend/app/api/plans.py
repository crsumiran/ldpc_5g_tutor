import json
from typing import Any
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from app.analysis import analyze_deterministic
from app.db import SessionLocal
from app.ingest.snapshot import snapshot_dir
from app.jobs import create_job, run_job
from app.models import Analysis, Plan, Project
from app.planning.generate import generate_plan_with_llm
from app.planning.manual import create_manual_plan
from app.planning.validate import validate_learning_plan
from app.schemas import LearningPlan, RepositoryAnalysis

router = APIRouter(prefix="/api", tags=["plans"])


class GeneratePlanRequest(BaseModel):
    notes: str | None = None


def _run_generate_plan_job(project_id: str, notes: str | None):
    db = SessionLocal()
    try:
        analysis_row = (
            db.query(Analysis)
            .filter(Analysis.project_id == project_id)
            .order_by(Analysis.created_at.desc())
            .first()
        )
        if not analysis_row:
            raise ValueError("Project must be analyzed before generating plan")
        analysis = RepositoryAnalysis.model_validate_json(analysis_row.json)

        snap = snapshot_dir(project_id)
        det = analyze_deterministic(snap)
        valid_paths = {item["path"] for item in det["inventory"]}

        plan = generate_plan_with_llm(
            analysis=analysis,
            valid_paths=valid_paths,
            notes=notes,
        )

        plan_row = Plan(
            project_id=project_id,
            json=plan.model_dump_json(),
            status="draft",
        )
        db.add(plan_row)
        db.commit()
        db.refresh(plan_row)
        return {"plan_id": plan_row.id, "plan": plan.model_dump()}
    finally:
        db.close()


@router.post("/projects/{project_id}/plans/generate")
def generate_plan_endpoint(
    project_id: str,
    req: GeneratePlanRequest,
    background_tasks: BackgroundTasks,
):
    db = SessionLocal()
    try:
        p = db.query(Project).filter(Project.id == project_id).first()
        if not p:
            raise HTTPException(status_code=404, detail="Project not found")

        job = create_job("generate_plan", db=db)
        background_tasks.add_task(run_job, job.id, _run_generate_plan_job, project_id, req.notes)
        return {"job_id": job.id}
    finally:
        db.close()


@router.post("/projects/{project_id}/plans/manual")
def create_manual_plan_endpoint(project_id: str, plan_data: LearningPlan):
    snap = snapshot_dir(project_id)
    valid_paths = None
    if snap.exists():
        det = analyze_deterministic(snap)
        valid_paths = {item["path"] for item in det["inventory"]}

    try:
        plan_row = create_manual_plan(
            project_id=project_id,
            plan_data=plan_data,
            valid_paths=valid_paths,
        )
        return {"id": plan_row.id, "status": plan_row.status, "plan": json.loads(plan_row.json)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/plans/{plan_id}")
def get_plan(plan_id: str):
    db = SessionLocal()
    try:
        plan_row = db.query(Plan).filter(Plan.id == plan_id).first()
        if not plan_row:
            raise HTTPException(status_code=404, detail="Plan not found")
        return {
            "id": plan_row.id,
            "project_id": plan_row.project_id,
            "status": plan_row.status,
            "plan": json.loads(plan_row.json),
            "created_at": str(plan_row.created_at),
            "updated_at": str(plan_row.updated_at),
        }
    finally:
        db.close()


@router.patch("/plans/{plan_id}")
def update_plan(plan_id: str, plan_data: LearningPlan):
    db = SessionLocal()
    try:
        plan_row = db.query(Plan).filter(Plan.id == plan_id).first()
        if not plan_row:
            raise HTTPException(status_code=404, detail="Plan not found")

        snap = snapshot_dir(plan_row.project_id)
        valid_paths = None
        if snap.exists():
            det = analyze_deterministic(snap)
            valid_paths = {item["path"] for item in det["inventory"]}

        ok, err_msg, val_plan = validate_learning_plan(plan_data, valid_paths=valid_paths)
        if not ok:
            raise HTTPException(status_code=400, detail=err_msg)

        plan_row.json = val_plan.model_dump_json()
        db.commit()
        return {"id": plan_row.id, "status": plan_row.status, "plan": val_plan.model_dump()}
    finally:
        db.close()


@router.post("/plans/{plan_id}/approve")
def approve_plan(plan_id: str):
    db = SessionLocal()
    try:
        plan_row = db.query(Plan).filter(Plan.id == plan_id).first()
        if not plan_row:
            raise HTTPException(status_code=404, detail="Plan not found")
        plan_row.status = "approved"
        db.commit()
        return {"id": plan_row.id, "status": "approved"}
    finally:
        db.close()
