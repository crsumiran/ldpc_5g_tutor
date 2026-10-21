import json
from pathlib import Path
from typing import Any
from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.analysis.llm_analyze import analyze_with_llm
from app.db import SessionLocal
from app.ingest import ingest_project
from app.ingest.snapshot import snapshot_dir
from app.jobs import create_job, run_job
from app.models import Analysis, Job, Project
from app.schemas import JobResponse

router = APIRouter(prefix="/api", tags=["projects"])


class LocalProjectRequest(BaseModel):
    path: str


class GitProjectRequest(BaseModel):
    url: str


@router.post("/projects/local")
def create_local_project(req: LocalProjectRequest):
    try:
        pid = ingest_project("local", path=req.path)
        db = SessionLocal()
        try:
            p = db.query(Project).filter(Project.id == pid).first()
            return {"id": p.id, "snapshot_hash": p.snapshot_hash, "snapshot_path": p.snapshot_path}
        finally:
            db.close()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/projects/git")
def create_git_project(req: GitProjectRequest):
    try:
        pid = ingest_project("git", url=req.url)
        db = SessionLocal()
        try:
            p = db.query(Project).filter(Project.id == pid).first()
            return {"id": p.id, "snapshot_hash": p.snapshot_hash, "snapshot_path": p.snapshot_path}
        finally:
            db.close()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/projects/upload")
async def create_upload_project(file: UploadFile = File(...)):
    try:
        content = await file.read()
        pid = ingest_project("upload", zip_source=content, filename=file.filename or "upload.zip")
        db = SessionLocal()
        try:
            p = db.query(Project).filter(Project.id == pid).first()
            return {"id": p.id, "snapshot_hash": p.snapshot_hash, "snapshot_path": p.snapshot_path}
        finally:
            db.close()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/projects")
def list_projects():
    db = SessionLocal()
    try:
        projects = db.query(Project).order_by(Project.created_at.desc()).all()
        return [
            {
                "id": p.id,
                "source_type": p.source_type,
                "source_uri": p.source_uri,
                "snapshot_hash": p.snapshot_hash,
                "created_at": str(p.created_at),
            }
            for p in projects
        ]
    finally:
        db.close()


@router.get("/projects/{project_id}")
def get_project(project_id: str):
    db = SessionLocal()
    try:
        p = db.query(Project).filter(Project.id == project_id).first()
        if not p:
            raise HTTPException(status_code=404, detail="Project not found")
        return {
            "id": p.id,
            "source_type": p.source_type,
            "source_uri": p.source_uri,
            "snapshot_hash": p.snapshot_hash,
            "snapshot_path": p.snapshot_path,
            "created_at": str(p.created_at),
        }
    finally:
        db.close()


def _run_analysis_job(project_id: str, snap_dir: Path):
    res = analyze_with_llm(snap_dir, project_id=project_id)
    return res.model_dump()


@router.post("/projects/{project_id}/analyze")
def start_project_analysis(project_id: str, background_tasks: BackgroundTasks):
    db = SessionLocal()
    try:
        p = db.query(Project).filter(Project.id == project_id).first()
        if not p:
            raise HTTPException(status_code=404, detail="Project not found")
        snap_dir = snapshot_dir(project_id)
        job = create_job("analyze", db=db)
        background_tasks.add_task(run_job, job.id, _run_analysis_job, project_id, snap_dir)
        return {"job_id": job.id}
    finally:
        db.close()


@router.get("/projects/{project_id}/analysis")
def get_project_analysis(project_id: str):
    db = SessionLocal()
    try:
        analysis = db.query(Analysis).filter(Analysis.project_id == project_id).order_by(Analysis.created_at.desc()).first()
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found for project")
        return json.loads(analysis.json)
    finally:
        db.close()


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job_status(job_id: str):
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        result = json.loads(job.result_json) if job.result_json else None
        return JobResponse(
            id=job.id,
            kind=job.kind,
            status=job.status,  # type: ignore
            error=job.error,
            result_json=result if isinstance(result, dict) else None,
        )
    finally:
        db.close()
