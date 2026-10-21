import shutil
import uuid
from pathlib import Path

from app.config import settings
from app.db import SessionLocal
from app.ingest.local import copy_tree_filtered
from app.models import Workspace
from app.schemas import AssignmentArtifact


def get_workspace_dir(project_id: str, workspace_id: str) -> Path:
    return Path(settings.data_dir) / "projects" / project_id / "learner" / workspace_id


def get_reference_dir(project_id: str, assignment_id: str) -> Path:
    return Path(settings.data_dir) / "projects" / project_id / "reference" / assignment_id


def get_hidden_dir(project_id: str, assignment_id: str) -> Path:
    return Path(settings.data_dir) / "projects" / project_id / "hidden" / assignment_id


def materialize_workspace(
    project_id: str,
    assignment: AssignmentArtifact,
    snapshot_path: Path,
    workspace_id: str | None = None,
) -> str:
    ws_id = workspace_id or str(uuid.uuid4())
    learner_dir = get_workspace_dir(project_id, ws_id)
    reference_dir = get_reference_dir(project_id, assignment.id)
    hidden_dir = get_hidden_dir(project_id, assignment.id)

    # 1. Clean destination and copy snapshot to learner workspace
    if learner_dir.exists():
        shutil.rmtree(learner_dir)
    copy_tree_filtered(snapshot_path, learner_dir)

    # 2. Save reference copy of modified files before overlaying starter files
    reference_dir.mkdir(parents=True, exist_ok=True)
    for sf in assignment.starter_files:
        orig = snapshot_path / sf.path
        if orig.exists() and orig.is_file():
            ref_dst = reference_dir / sf.path
            ref_dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(orig, ref_dst)

    # 3. Overlay starter files in learner workspace
    for sf in assignment.starter_files:
        dst = learner_dir / sf.path
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(sf.content, encoding="utf-8")

    # 4. Write public tests into learner workspace
    for pt in assignment.public_tests:
        dst = learner_dir / pt.path
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(pt.content, encoding="utf-8")

    # 5. Save hidden tests OUTSIDE learner workspace
    if hidden_dir.exists():
        shutil.rmtree(hidden_dir)
    hidden_dir.mkdir(parents=True, exist_ok=True)
    for ht in assignment.hidden_tests:
        dst = hidden_dir / ht.path
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(ht.content, encoding="utf-8")

    # 6. Record in DB
    db = SessionLocal()
    try:
        ws_row = Workspace(
            id=ws_id,
            assignment_id=assignment.id,
            path=str(learner_dir),
        )
        db.add(ws_row)
        db.commit()
    finally:
        db.close()

    return ws_id
