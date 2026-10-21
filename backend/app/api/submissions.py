import json
from pathlib import Path
from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.assignments.workspace import get_hidden_dir
from app.db import SessionLocal
from app.eval.evaluate import evaluate_submission
from app.jobs import create_job, run_job
from app.models import Assignment, Plan, Progress, Submission, Workspace
from app.schemas import AssignmentArtifact, ChatRequest, ChatResponse
from app.tutor.chat import handle_chat

router = APIRouter(prefix="/api", tags=["submissions"])


def _run_evaluate_job(workspace_id: str, assignment: AssignmentArtifact, project_id: str, assignment_id: str, code: str | None, target_path: str):
    db = SessionLocal()
    try:
        ws_row = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        if not ws_row:
            raise ValueError("Workspace not found")

        workspace_path = Path(ws_row.path)

        # If code provided, write it into the workspace
        if code:
            target = workspace_path / target_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(code, encoding="utf-8")

        hidden_dir = get_hidden_dir(project_id, assignment_id)
        evaluation = evaluate_submission(
            project_id=project_id,
            workspace_path=workspace_path,
            assignment=assignment,
            hidden_dir=hidden_dir,
        )

        # Record submission + progress
        sub = Submission(workspace_id=workspace_id, evaluation_json=evaluation.model_dump_json())
        db.add(sub)

        prog = db.query(Progress).filter(Progress.assignment_id == assignment_id).first()
        if prog:
            if evaluation.passed:
                prog.passed = True
        else:
            prog = Progress(assignment_id=assignment_id, passed=evaluation.passed)
            db.add(prog)
        db.commit()

        return {"passed": evaluation.passed, "evaluation": evaluation.model_dump()}
    finally:
        db.close()


@router.post("/assignments/{assignment_id}/submissions")
def submit_assignment(
    assignment_id: str,
    body: dict,
    background_tasks: BackgroundTasks,
):
    db = SessionLocal()
    try:
        a_row = db.query(Assignment).filter(Assignment.id == assignment_id).first()
        if not a_row:
            raise HTTPException(status_code=404, detail="Assignment not found")
        plan_row = db.query(Plan).filter(Plan.id == a_row.plan_id).first()
        if not plan_row:
            raise HTTPException(status_code=404, detail="Plan not found")

        ws_row = db.query(Workspace).filter(Workspace.assignment_id == assignment_id).first()
        if not ws_row:
            raise HTTPException(status_code=400, detail="No workspace created yet. Call POST /assignments/{id}/workspace first.")

        art = AssignmentArtifact.model_validate_json(a_row.artifact_json)
        code = body.get("code")
        target_path = art.starter_files[0].path if art.starter_files else ""

        job = create_job("evaluate", db=db)
        background_tasks.add_task(
            run_job,
            job.id,
            _run_evaluate_job,
            ws_row.id,
            art,
            plan_row.project_id,
            assignment_id,
            code,
            target_path,
        )
        return {"job_id": job.id}
    finally:
        db.close()


@router.post("/assignments/{assignment_id}/chat", response_model=ChatResponse)
def chat_endpoint(assignment_id: str, req: ChatRequest):
    try:
        return handle_chat(assignment_id, req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))