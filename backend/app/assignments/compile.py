import ast
import json
from pathlib import Path
from typing import Any

from app.assignments.leakcheck import assert_no_leak
from app.config import settings
from app.db import SessionLocal
from app.llm import complete_json
from app.models import Assignment
from app.schemas import AssignmentArtifact, FileBlob, PlanAssignment

PROMPT_FILE = Path("/home/ranga/opencode/tutor/backend/prompts/assignment_compiler.txt")


def compile_assignment(
    plan_id: str,
    plan_assignment: PlanAssignment,
    snapshot: Path,
    model: str | None = None,
) -> AssignmentArtifact:
    reference_files: list[FileBlob] = []
    for sf in plan_assignment.source_files:
        p = snapshot / sf
        if p.exists() and p.is_file():
            try:
                content = p.read_text(encoding="utf-8", errors="replace")
                reference_files.append(FileBlob(path=sf, content=content))
            except Exception:
                pass

    system_prompt = PROMPT_FILE.read_text(encoding="utf-8")
    user_payload = {
        "assignment_plan": plan_assignment.model_dump(),
        "reference_files": [rf.model_dump() for rf in reference_files],
    }

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Compile this assignment into a CS231n-style assignment:\n\n{json.dumps(user_payload, indent=2)}"},
    ]

    raw_json = complete_json(messages, model=model or settings.planner_model)
    artifact = AssignmentArtifact.model_validate(raw_json)

    # Validate Python syntax for starter files
    for sf in artifact.starter_files:
        if sf.path.endswith(".py"):
            try:
                ast.parse(sf.content, filename=sf.path)
            except SyntaxError as e:
                raise ValueError(f"Syntax error in compiled starter file '{sf.path}': {e}")

    # Run leak check
    assert_no_leak(artifact, reference_files)

    # Save or update in database
    db = SessionLocal()
    try:
        existing = db.query(Assignment).filter(Assignment.id == artifact.id).first()
        if existing:
            existing.plan_id = plan_id
            existing.artifact_json = artifact.model_dump_json()
        else:
            assignment_row = Assignment(
                id=artifact.id,
                plan_id=plan_id,
                artifact_json=artifact.model_dump_json(),
                published=False,
            )
            db.add(assignment_row)
        db.commit()
    finally:
        db.close()

    return artifact
