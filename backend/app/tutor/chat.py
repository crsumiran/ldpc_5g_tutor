import json
import os
from pathlib import Path
from typing import Any

from app.assignments.leakcheck import strip_reference_leak
from app.assignments.workspace import get_hidden_dir, get_reference_dir, get_workspace_dir
from app.config import settings
from app.db import SessionLocal
from app.eval.evaluate import evaluate_submission
from app.llm import complete
from app.models import Assignment, Conversation, Plan, Progress, Workspace
from app.schemas import AssignmentArtifact, ChatRequest, ChatResponse, Evaluation, FileBlob
from app.tutor.prompt import get_tutor_system_prompt


def handle_chat(
    assignment_id: str,
    req: ChatRequest,
    model: str | None = None,
) -> ChatResponse:
    db = SessionLocal()
    artifact: AssignmentArtifact | None = None
    project_id: str | None = None
    workspace_path: Path | None = None
    reference_files: list[FileBlob] = []

    try:
        assignment_row = db.query(Assignment).filter(Assignment.id == assignment_id).first()
        if assignment_row:
            artifact = AssignmentArtifact.model_validate_json(assignment_row.artifact_json)
            plan_row = db.query(Plan).filter(Plan.id == assignment_row.plan_id).first()
            if plan_row:
                project_id = plan_row.project_id

        # Look for the most recent workspace
        ws_row = (
            db.query(Workspace)
            .filter(Workspace.assignment_id == assignment_id)
            .order_by(Workspace.created_at.desc())
            .first()
        )
        if ws_row and Path(ws_row.path).exists():
            workspace_path = Path(ws_row.path)

        # Load reference files for leak prevention
        if project_id:
            ref_dir = get_reference_dir(project_id, assignment_id)
            if ref_dir.exists():
                for root, _, files in os.walk(ref_dir):
                    for f in files:
                        p = Path(root) / f
                        try:
                            rel = str(p.relative_to(ref_dir))
                            reference_files.append(FileBlob(path=rel, content=p.read_text(encoding="utf-8", errors="ignore")))
                        except Exception:
                            pass
    finally:
        db.close()

    evaluation: Evaluation | None = None
    passed = False

    # If code submitted and we have an artifact and workspace, evaluate it
    if req.code and artifact and workspace_path and project_id:
        # Write student code to first starter file path
        if artifact.starter_files:
            target_rel = artifact.starter_files[0].path
            target_path = workspace_path / target_rel
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(req.code, encoding="utf-8")

        hidden_dir = get_hidden_dir(project_id, assignment_id)
        evaluation = evaluate_submission(
            project_id=project_id,
            workspace_path=workspace_path,
            assignment=artifact,
            hidden_dir=hidden_dir,
        )
        passed = evaluation.passed

        # Update progress in DB
        db = SessionLocal()
        try:
            prog = db.query(Progress).filter(Progress.assignment_id == assignment_id).first()
            if prog:
                if passed:
                    prog.passed = True
            else:
                prog = Progress(assignment_id=assignment_id, passed=passed)
                db.add(prog)
            db.commit()
        finally:
            db.close()

    # Build prompt context (learner-visible only)
    system_prompt = get_tutor_system_prompt()
    assignment_context = {}
    if artifact:
        assignment_context = {
            "id": artifact.id,
            "title": artifact.title,
            "business_context": artifact.business_context,
            "task": artifact.task,
            "approach": artifact.approach,
            "hints": artifact.hints,
            "public_tests": [pt.path for pt in artifact.public_tests],
        }

    system_message = (
        f"{system_prompt}\n\n"
        f"--- CURRENT ASSIGNMENT CONTEXT ---\n"
        f"{json.dumps(assignment_context, indent=2)}"
    )

    messages: list[dict[str, Any]] = [{"role": "system", "content": system_message}]
    messages.extend(req.history)

    user_text = req.message
    if req.code:
        user_text += f"\n\n<student_submission>\n{req.code}\n</student_submission>"
    if evaluation:
        user_text += f"\n\n<evaluation_report>\n{evaluation.model_dump_json(indent=2)}\n</evaluation_report>"

    messages.append({"role": "user", "content": user_text})

    llm_reply = complete(
        messages=messages,
        model=model or settings.tutor_model,
        temperature=0.3,
    )
    raw_content = llm_reply.get("content") or ""
    clean_reply = strip_reference_leak(raw_content, reference_files)

    # Record conversation in DB
    db = SessionLocal()
    try:
        conv = db.query(Conversation).filter(Conversation.assignment_id == assignment_id).first()
        curr_history = json.loads(conv.json) if conv and conv.json else []
        curr_history.append({"role": "user", "content": req.message})
        curr_history.append({"role": "assistant", "content": clean_reply})

        if conv:
            conv.json = json.dumps(curr_history)
        else:
            conv = Conversation(assignment_id=assignment_id, json=json.dumps(curr_history))
            db.add(conv)
        db.commit()
    finally:
        db.close()

    return ChatResponse(
        reply=clean_reply,
        passed=passed,
        evaluation=evaluation,
        executor_output=evaluation.public.output if evaluation else None,
    )
