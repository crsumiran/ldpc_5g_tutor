from typing import Any
from app.db import SessionLocal
from app.ingest.git import ingest_git
from app.ingest.local import ingest_local
from app.ingest.snapshot import new_project_id
from app.ingest.zip import ingest_zip
from app.models import Project


def ingest_project(kind: str, **kwargs: Any) -> str:
    pid = kwargs.get("project_id") or new_project_id()

    if kind == "local":
        path = kwargs["path"]
        pid, snap_hash, snap_path = ingest_local(path, project_id=pid)
        uri = str(path)
    elif kind == "git":
        url = kwargs["url"]
        pid, snap_hash, snap_path = ingest_git(url, project_id=pid)
        uri = url
    elif kind in ("zip", "upload"):
        zip_source = kwargs.get("file") or kwargs.get("zip_source")
        uri = kwargs.get("filename", "upload.zip")
        pid, snap_hash, snap_path = ingest_zip(zip_source, project_id=pid)
    else:
        raise ValueError(f"Unknown ingest kind: {kind}")

    db = SessionLocal()
    try:
        project = Project(
            id=pid,
            source_type=kind,
            source_uri=uri,
            snapshot_hash=snap_hash,
            snapshot_path=snap_path,
        )
        db.add(project)
        db.commit()
    finally:
        db.close()

    return pid
