import hashlib
import os
import uuid
from pathlib import Path

from app.config import settings


def new_project_id() -> str:
    return str(uuid.uuid4())


def project_base_dir(project_id: str) -> Path:
    return Path(settings.data_dir) / "projects" / project_id


def snapshot_dir(project_id: str) -> Path:
    return project_base_dir(project_id) / "source"


def refuse_symlink_escape(root: Path) -> None:
    resolved_root = root.resolve()
    for root_dir, dirs, files in os.walk(root, followlinks=False):
        for item in dirs + files:
            p = Path(root_dir) / item
            if p.is_symlink():
                target = p.resolve()
                try:
                    target.relative_to(resolved_root)
                except ValueError:
                    raise ValueError(f"Symlink escapes root: {p} -> {target}")


def hash_tree(path: Path) -> str:
    sha = hashlib.sha256()
    file_paths: list[Path] = []
    for root_dir, _, files in os.walk(path):
        for f in files:
            file_paths.append(Path(root_dir) / f)

    # Sort deterministically by relative path
    for fp in sorted(file_paths, key=lambda p: str(p.relative_to(path))):
        rel_str = str(fp.relative_to(path))
        sha.update(rel_str.encode("utf-8"))
        try:
            content = fp.read_bytes()
            sha.update(content)
        except (OSError, PermissionError):
            pass

    return sha.hexdigest()
