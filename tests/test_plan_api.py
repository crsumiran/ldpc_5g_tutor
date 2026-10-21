from unittest.mock import patch
from fastapi.testclient import TestClient

from app.db import SessionLocal
from app.main import app
from app.models import Plan, Project

client = TestClient(app)
FIXTURE_PATH = "/home/ranga/opencode/tutor/fixtures/python_etl"


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_local_ingest_and_reference_separation_workflow():
    # 1. Ingest local project
    r = client.post("/api/projects/local", json={"path": FIXTURE_PATH})
    assert r.status_code == 200
    project_id = r.json()["id"]

    # 2. List projects
    r = client.get("/api/projects")
    assert r.status_code == 200
    assert any(p["id"] == project_id for p in r.json())

    # 3. Get project
    r = client.get(f"/api/projects/{project_id}")
    assert r.status_code == 200
    assert r.json()["source_type"] == "local"


def test_plan_approve_and_manual_plan():
    db = SessionLocal()
    try:
        # Seed a project
        proj = Project(
            id="proj-plans",
            source_type="local",
            source_uri=FIXTURE_PATH,
            snapshot_hash="h",
            snapshot_path=FIXTURE_PATH,
        )
        db.merge(proj)
        db.commit()
    finally:
        db.close()

    manual_plan = {
        "title": "Orders Pipeline",
        "learner_level": "python_comfortable",
        "status": "draft",
        "assignments": [
            {
                "id": "DE-001",
                "title": "Normalize orders",
                "prerequisites": [],
                "concepts": ["pandas"],
                "source_files": ["src/orders/normalize.py"],
                "estimated_minutes": 45,
                "difficulty": "medium",
                "adapter": "python_pytest",
            }
        ],
    }

    r = client.post("/api/projects/proj-plans/plans/manual", json=manual_plan)
    assert r.status_code == 200
    plan_id = r.json()["id"]

    # Approve plan
    r = client.post(f"/api/plans/{plan_id}/approve")
    assert r.status_code == 200
    assert r.json()["status"] == "approved"

    # Get plan
    r = client.get(f"/api/plans/{plan_id}")
    assert r.status_code == 200
    assert r.json()["plan"]["title"] == "Orders Pipeline"