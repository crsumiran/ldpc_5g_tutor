import shutil
from pathlib import Path

from app.config import settings
from app.ingest.snapshot import (
    hash_tree,
    new_project_id,
    refuse_symlink_escape,
    snapshot_dir,
)

EXCLUDE_PATTERNS = {".git", "__pycache__", ".venv", "node_modules", ".pytest_cache"}


def is_path_allowed(src_path: Path, allowed_roots_str: str) -> bool:
    resolved_src = src_path.resolve()
    allowed_roots = [
        Path(r.strip()).resolve()
        for r in allowed_roots_str.split(":")
        if r.strip()
    ]
    for root in allowed_roots:
        try:
            resolved_src.relative_to(root)
            return True
        except ValueError:
            pass
    return False


def copy_tree_filtered(src: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        if item.name in EXCLUDE_PATTERNS or item.name.endswith(".pyc"):
            continue
        dest_item = dest / item.name
        if item.is_dir() and not item.is_symlink():
            copy_tree_filtered(item, dest_item)
        elif item.is_symlink():
            # Copy symlink as symlink
            target = item.readlink()
            dest_item.symlink_to(target)
        else:
            shutil.copy2(item, dest_item)


def ingest_local(source_path: str | Path, project_id: str | None = None) -> tuple[str, str, str]:
    src = Path(source_path)
    if not src.exists() or not src.is_dir():
        raise ValueError(f"Source directory does not exist: {source_path}")

    if not is_path_allowed(src, settings.allowed_import_roots):
        raise PermissionError(f"Import path '{source_path}' is outside allowed roots: {settings.allowed_import_roots}")

    pid = project_id or new_project_id()
    dest = snapshot_dir(pid)
    if dest.exists():
        shutil.rmtree(dest)

    copy_tree_filtered(src, dest)
    refuse_symlink_escape(dest)
    snap_hash = hash_tree(dest)
    return pid, snap_hash, str(dest)
