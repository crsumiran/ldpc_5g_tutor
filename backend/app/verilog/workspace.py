import json
import shutil
import uuid
from pathlib import Path

from app.config import settings
from app.verilog.manifest import get_checkpoint
from app.verilog.schemas import CourseManifest


MAX_FILE_BYTES = 256 * 1024


def lab_workspace_dir(session_id: str) -> Path:
    return Path(settings.data_dir) / "labs" / session_id / "workspace"


def lab_artifact_dir(run_id: str) -> Path:
    return Path(settings.data_dir) / "labs" / "runs" / run_id


def _safe_path(root: Path, relative: str) -> Path:
    candidate = (root / relative).resolve()
    if Path(relative).is_absolute() or ".." in Path(relative).parts or not candidate.is_relative_to(root.resolve()):
        raise ValueError("unsafe file path")
    return candidate


def materialize_lab_workspace(course_root: Path, manifest: CourseManifest, session_id: str | None = None) -> tuple[str, Path]:
    sid = session_id or str(uuid.uuid4())
    destination = lab_workspace_dir(sid)
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)

    for checkpoint in manifest.checkpoints:
        for relative in checkpoint.source_files:
            source = _safe_path(course_root / "starter", relative)
            if source.is_file():
                target = _safe_path(destination, relative)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
    for relative in manifest.provided_files:
        source = _safe_path(course_root, relative)
        target = _safe_path(destination, relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return sid, destination


def allowed_editable_files(manifest: CourseManifest, passed_ids: set[str], checkpoint_id: str) -> set[str]:
    allowed: set[str] = set()
    for checkpoint in manifest.checkpoints:
        if checkpoint.id == checkpoint_id or checkpoint.id in passed_ids or (
            manifest.toolchain == "python" and set(checkpoint.prerequisites).issubset(passed_ids)
        ):
            allowed.update(checkpoint.editable_files)
    return allowed


def ensure_lab_workspace_assets(course_root: Path, manifest: CourseManifest, workspace: Path) -> None:
    """Add newly declared Python assets; never overwrite learner work or progress."""
    if manifest.toolchain != "python":
        return
    assets = {relative: course_root / "starter" / relative
              for checkpoint in manifest.checkpoints for relative in checkpoint.source_files}
    assets.update({relative: course_root / relative for relative in manifest.provided_files})
    if workspace.is_symlink():
        raise ValueError("workspace must not be a symlink")
    for relative, source in assets.items():
        lexical = workspace / relative
        if any(part.is_symlink() for part in [lexical, *lexical.parents] if part != workspace.parent):
            raise ValueError("workspace assets must not use symlinks")
        target = _safe_path(workspace, relative)
        if target.exists():
            continue
        if source.is_symlink() or not source.resolve().is_relative_to(course_root.resolve()):
            raise ValueError("unsafe starter asset")
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            with target.open("xb") as destination, source.open("rb") as original:
                shutil.copyfileobj(original, destination)
        except FileExistsError:
            pass


def read_workspace_file(workspace: Path, relative: str) -> str:
    path = _safe_path(workspace, relative)
    if not path.is_file():
        raise FileNotFoundError(relative)
    if path.stat().st_size > MAX_FILE_BYTES:
        raise ValueError("file is too large")
    return path.read_text(encoding="utf-8", errors="replace")


def write_workspace_file(workspace: Path, relative: str, content: str) -> None:
    if len(content.encode("utf-8")) > MAX_FILE_BYTES:
        raise ValueError("file is too large")
    path = _safe_path(workspace, relative)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def progress_ids(progress_json: str) -> set[str]:
    try:
        value = json.loads(progress_json or "{}")
        return set(value.get("passed", []))
    except (TypeError, ValueError):
        return set()


def progress_json(passed_ids: set[str]) -> str:
    return json.dumps({"passed": sorted(passed_ids)})
