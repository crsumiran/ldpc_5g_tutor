import io
import shutil
import zipfile
from pathlib import Path
from typing import BinaryIO

from app.ingest.snapshot import (
    hash_tree,
    new_project_id,
    refuse_symlink_escape,
    snapshot_dir,
)

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MiB
MAX_TOTAL_SIZE = 50 * 1024 * 1024  # 50 MiB
EXCLUDE_DIRS = {".git", "__pycache__", ".venv", "node_modules"}


def ingest_zip(
    zip_source: BinaryIO | bytes | str | Path,
    project_id: str | None = None,
) -> tuple[str, str, str]:
    if isinstance(zip_source, (str, Path)):
        zf = zipfile.ZipFile(zip_source, "r")
    elif isinstance(zip_source, bytes):
        zf = zipfile.ZipFile(io.BytesIO(zip_source), "r")
    else:
        zf = zipfile.ZipFile(zip_source, "r")

    pid = project_id or new_project_id()
    dest = snapshot_dir(pid)
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)

    try:
        total_size = 0
        infolist = zf.infolist()

        # Pre-validate all entries before writing anything
        for info in infolist:
            filename = info.filename

            # Check absolute path
            if filename.startswith("/") or filename.startswith("\\"):
                raise ValueError(f"Absolute path in ZIP entry: {filename}")

            parts = Path(filename).parts
            if ".." in parts:
                raise ValueError(f"Path traversal ('..') in ZIP entry: {filename}")

            if info.file_size > MAX_FILE_SIZE:
                raise ValueError(f"File '{filename}' exceeds max file size of 5 MiB ({info.file_size} bytes)")

            total_size += info.file_size
            if total_size > MAX_TOTAL_SIZE:
                raise ValueError(f"ZIP uncompressed content exceeds max total size of 50 MiB ({total_size} bytes)")

        # Safe extraction
        for info in infolist:
            filename = info.filename
            parts = Path(filename).parts
            if any(part in EXCLUDE_DIRS for part in parts) or filename.endswith(".pyc"):
                continue

            target_path = dest / filename
            if info.is_dir():
                target_path.mkdir(parents=True, exist_ok=True)
            else:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(info) as src, open(target_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)

        refuse_symlink_escape(dest)
        snap_hash = hash_tree(dest)
        return pid, snap_hash, str(dest)
    finally:
        zf.close()
