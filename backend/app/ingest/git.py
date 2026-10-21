import shutil
import subprocess
import tempfile
from pathlib import Path

from app.ingest.local import copy_tree_filtered
from app.ingest.snapshot import (
    hash_tree,
    new_project_id,
    refuse_symlink_escape,
    snapshot_dir,
)


def ingest_git(url: str, project_id: str | None = None) -> tuple[str, str, str]:
    # Check if git is available
    if not shutil.which("git"):
        raise RuntimeError("git executable not found on system")

    pid = project_id or new_project_id()
    dest = snapshot_dir(pid)
    if dest.exists():
        shutil.rmtree(dest)

    with tempfile.TemporaryDirectory(prefix="git-clone-") as tmp:
        tmp_path = Path(tmp) / "repo"
        cmd = [
            "git",
            "clone",
            "--depth",
            "1",
            "--single-branch",
            "--recurse-submodules=no",
            url,
            str(tmp_path),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"Git clone failed: {res.stderr}")

        copy_tree_filtered(tmp_path, dest)

    refuse_symlink_escape(dest)
    snap_hash = hash_tree(dest)
    return pid, snap_hash, str(dest)
