import json
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.db import SessionLocal
from app.main import app
from app.models import Analysis, Assignment, Plan, Project

client = TestClient(app)
FIXTURE_PATH = "/home/ranga/opencode/tutor/fixtures/python_etl"

GOOD_ARTIFACT = {
    "id": "DE-001",
    "title": "Normalize Orders",
    "business_context": "Orders pipeline",
    "objectives": ["Normalize orders"],
    "concepts": ["pandas"],
    "inspect_files": ["src/orders/normalize.py"],
    "task": "Implement normalization",
    "approach": ["Step 1", "Step 2"],
    "starter_files": [
        {
            "path": "src/orders/normalize.py",
            "content": "import pandas as pd\nORDER_SCHEMA = ['order_id', 'ts_utc', 'amount']\ndef normalize_orders(df):\n    # TODO: implement\n    raise NotImplementedError\n",
        }
    ],
    "public_tests": [
        {
            "path": "tests/test_normalize.py",
            "content": "import pandas as pd\nfrom src.orders.normalize import normalize_orders\ndef test_n():\n    df = pd.DataFrame({'order_id':['O1'],'order_date':['2026-01-01'],'amount':[1.0]})\n    assert len(normalize_orders(df)) == 1\n",
        }
    ],
    "hidden_tests": [
        {
            "path": "tests/test_hidden.py",
            "content": "import pandas as pd\nfrom src.orders.normalize import normalize_orders\ndef test_h():\n    df = pd.DataFrame({'order_id':['O1'],'order_date':['2026-01-01'],'amount':[1.0]})\n    assert list(normalize_orders(df).columns) == ['order_id','ts_utc','amount']\n",
        }
    ],
    "run_command": ["pytest", "tests/test_normalize.py", "-q"],
    "hints": ["hint1", "hint2", "hint3"],
    "rubric": [{"name": "correctness", "weight": 1.0}],
    "acceptance": ["pass"],
    "estimated_minutes": 45,
    "adapter": "python_pytest",
}

FAKE_ANALYSIS = {
    "project_summary": "Orders ETL",
    "stack": ["Python", "pytest"],
    "components": [],
    "data_flows": [],
    "development_commands": [],
    "important_files": [{"path": "src/orders/normalize.py", "reason": "core", "bytes": 100}],
    "detected_adapters": ["python_pytest"],
    "risks": [],
    "unknowns": [],
}


def _seed_project_plan():
    db = SessionLocal()
    try:
        proj = Project(
            id="proj-wf",
            source_type="local",
            source_uri=FIXTURE_PATH,
            snapshot_hash="h",
            snapshot_path=FIXTURE_PATH,
        )
        db.merge(proj)
        plan = Plan(
            id="plan-wf",
            project_id="proj-wf",
            json='{"title":"Orders","learner_level":"python_comfortable","status":"draft","assignments":[{"id":"DE-001","title":"Normalize orders","prerequisites":[],"concepts":["pandas"],"source_files":["src/orders/normalize.py"],"estimated_minutes":45,"difficulty":"medium","adapter":"python_pytest"}]}',
            status="draft",
        )
        db.merge(plan)
        db.commit()
    finally:
        db.close()


def test_assignment_compile_and_learner_view_hides_hidden_tests():
    _seed_project_plan()

    # Compile assignments via generate endpoint (LLM mocked)
    with patch("app.planning.generate.complete_json", return_value=FAKE_ANALYSIS):
        pass

    # Directly compile through the compiler with mocked LLM
    with patch("app.assignments.compile.complete_json", return_value=GOOD_ARTIFACT):
        db = SessionLocal()
        try:
            from app.assignments.compile import compile_assignment
            from app.schemas import PlanAssignment
            from pathlib import Path
            pa = PlanAssignment(id="DE-001", title="Normalize orders", source_files=["src/orders/normalize.py"], adapter="python_pytest")
            compile_assignment("plan-wf", pa, Path(FIXTURE_PATH))
        finally:
            db.close()

    # Mentor view includes hidden_tests
    r = client.get("/api/assignments/DE-001", params={"view": "mentor"})
    assert r.status_code == 200
    assert len(r.json()["hidden_tests"]) == 1

    # Learner view hides hidden_tests
    r = client.get("/api/assignments/DE-001", params={"view": "learner"})
    assert r.status_code == 200
    assert "hidden_tests" not in r.json()

    # Publish assignment
    r = client.post("/api/assignments/DE-001/publish")
    assert r.status_code == 200
    assert r.json()["published"] is True


def test_workspace_creation():
    _seed_project_plan()
    with patch("app.assignments.compile.complete_json", return_value=GOOD_ARTIFACT):
        db = SessionLocal()
        try:
            from app.assignments.compile import compile_assignment
            from app.schemas import PlanAssignment
            from pathlib import Path
            pa = PlanAssignment(id="DE-001", title="Normalize orders", source_files=["src/orders/normalize.py"], adapter="python_pytest")
            compile_assignment("plan-wf", pa, Path(FIXTURE_PATH))
        finally:
            db.close()

    r = client.post("/api/assignments/DE-001/workspace")
    assert r.status_code == 200
    assert "workspace_id" in r.json()