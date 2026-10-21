import io
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
import pytest

from app.db import SessionLocal
from app.ingest import ingest_project
from app.ingest.local import ingest_local
from app.ingest.snapshot import snapshot_dir
from app.ingest.zip import ingest_zip
from app.models import Project

FIXTURES = Path("/home/ranga/opencode/tutor/fixtures")


def test_local_ingest_success_and_hash_stability():
    src = FIXTURES / "python_etl"
    pid1, hash1, path1 = ingest_local(src)
    pid2, hash2, path2 = ingest_local(src)

    assert hash1 == hash2
    assert Path(path1).exists()
    assert (Path(path1) / "src" / "hello.py").exists()

    # Ingest through ingest_project to verify DB row creation
    pid3 = ingest_project("local", path=str(src))
    db = SessionLocal()
    try:
        p = db.query(Project).filter(Project.id == pid3).first()
        assert p is not None
        assert p.snapshot_hash == hash1
    finally:
        db.close()


def test_local_ingest_outside_allowed_roots_raises():
    with tempfile.TemporaryDirectory(dir="/tmp") as tmp_outside:
        p = Path(tmp_outside) / "sample"
        p.mkdir()
        (p / "test.txt").write_text("hello")
        with pytest.raises(PermissionError):
            ingest_local(p)


def test_zip_traversal_raises():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("../evil.py", "malicious_payload = True")
    buf.seek(0)

    with pytest.raises(ValueError, match=r"Path traversal"):
        ingest_zip(buf.getvalue())


def test_zip_absolute_path_raises():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("/etc/passwd", "root:x:0:0")
    buf.seek(0)

    with pytest.raises(ValueError, match=r"Absolute path"):
        ingest_zip(buf.getvalue())


def test_git_ingest_local_repo():
    if not shutil.which("git"):
        pytest.skip("git not installed")

    with tempfile.TemporaryDirectory(prefix="git-fixture-") as tmp:
        repo_dir = Path(tmp) / "repo"
        repo_dir.mkdir()
        subprocess.run(["git", "init", str(repo_dir)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(repo_dir), "config", "user.name", "Test"], check=True)
        subprocess.run(["git", "-C", str(repo_dir), "config", "user.email", "test@example.com"], check=True)
        (repo_dir / "README.md").write_text("# Test Git Repo")
        subprocess.run(["git", "-C", str(repo_dir), "add", "."], check=True)
        subprocess.run(["git", "-C", str(repo_dir), "commit", "-m", "initial commit"], check=True)

        pid = ingest_project("git", url=str(repo_dir))
        snap = snapshot_dir(pid)
        assert (snap / "README.md").exists()
        assert not (snap / ".git").exists()
