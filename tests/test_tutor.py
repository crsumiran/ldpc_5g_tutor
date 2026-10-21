from pathlib import Path
from unittest.mock import patch

from app.assignments.workspace import materialize_workspace
from app.db import SessionLocal
from app.models import Assignment, Plan, Project
from app.schemas import AssignmentArtifact, ChatRequest, FileBlob
from app.tutor.chat import handle_chat

FIXTURES = Path("/home/ranga/opencode/tutor/fixtures")


def test_tutor_strips_reference_leaks_and_verifies_passed():
    project_id = "test-proj-tutor"
    plan_id = "test-plan-tutor"
    assignment_id = "DE-001"

    db = SessionLocal()
    try:
        # Seed project and plan
        proj = Project(
            id=project_id,
            source_type="local",
            source_uri=str(FIXTURES / "python_etl"),
            snapshot_hash="h1",
            snapshot_path=str(FIXTURES / "python_etl"),
        )
        db.merge(proj)

        plan = Plan(
            id=plan_id,
            project_id=project_id,
            json="{}",
            status="approved",
        )
        db.merge(plan)
        db.commit()
    finally:
        db.close()

    artifact = AssignmentArtifact(
        id=assignment_id,
        title="Normalize Orders",
        business_context="Orders pipeline",
        objectives=["Normalize orders"],
        concepts=["pandas"],
        inspect_files=["src/orders/normalize.py"],
        task="Implement normalization",
        approach=["Step 1", "Step 2"],
        starter_files=[
            FileBlob(
                path="src/orders/normalize.py",
                content="def normalize_orders(df):\n    # TODO: implement\n    raise NotImplementedError\n",
            )
        ],
        public_tests=[
            FileBlob(
                path="tests/test_normalize.py",
                content="""import pandas as pd
from src.orders.normalize import normalize_orders

def test_normalize():
    df = pd.DataFrame({'order_id': ['O1'], 'order_date': ['2026-01-01'], 'amount': [100.0]})
    res = normalize_orders(df)
    assert len(res) == 1
""",
            )
        ],
        hidden_tests=[],
        run_command=["pytest", "tests/test_normalize.py", "-q"],
        hints=["h1", "h2", "h3"],
        rubric=[{"name": "correctness", "weight": 1.0}],
        acceptance=["pass"],
        estimated_minutes=45,
        adapter="python_pytest",
    )

    db = SessionLocal()
    try:
        a_row = Assignment(
            id=assignment_id,
            plan_id=plan_id,
            artifact_json=artifact.model_dump_json(),
            published=True,
        )
        db.merge(a_row)
        db.commit()
    finally:
        db.close()

    materialize_workspace(
        project_id=project_id,
        assignment=artifact,
        snapshot_path=FIXTURES / "python_etl",
    )

    # Mock complete to return text containing 3 lines of reference code from normalize.py
    leaking_reply = {
        "content": (
            "Here is a great hint! You should do:\n"
            "normalized['ts_utc'] = pd.to_datetime(normalized['order_date'], utc=True)\n"
            "normalized = normalized.dropna(subset=['order_id'])\n"
            "normalized = normalized[normalized['order_id'].astype(str).str.strip() != '']\n"
            "And you're done!"
        )
    }

    req = ChatRequest(
        assignment_id=assignment_id,
        message="I need help with normalize_orders",
        code="def normalize_orders(df):\n    # TODO\n    raise NotImplementedError\n",
    )

    with patch("app.tutor.chat.complete", return_value=leaking_reply):
        res = handle_chat(assignment_id, req)

        # Evaluator ran on starter code which raises NotImplementedError -> passed must be False
        assert res.passed is False
        assert res.evaluation is not None

        # The response must have stripped the leaked reference lines
        assert "I cannot provide the full solution" in res.reply
        assert "dropna" not in res.reply
