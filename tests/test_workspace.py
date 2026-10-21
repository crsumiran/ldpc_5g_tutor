from pathlib import Path

from app.assignments.workspace import (
    get_hidden_dir,
    get_reference_dir,
    get_workspace_dir,
    materialize_workspace,
)
from app.schemas import AssignmentArtifact, FileBlob

FIXTURES = Path("/home/ranga/opencode/tutor/fixtures")


def test_materialize_workspace_separation():
    project_id = "test-proj-workspace"
    artifact = AssignmentArtifact(
        id="DE-001",
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
                content="def test_normalize(): pass\n",
            )
        ],
        hidden_tests=[
            FileBlob(
                path="tests/test_hidden_edge_cases.py",
                content="def test_hidden(): pass\n",
            )
        ],
        run_command=["pytest", "tests/test_normalize.py", "-q"],
        hints=["h1", "h2", "h3"],
        rubric=[{"name": "correctness", "weight": 1.0}],
        acceptance=["pass"],
        estimated_minutes=45,
        adapter="python_pytest",
    )

    ws_id = materialize_workspace(
        project_id=project_id,
        assignment=artifact,
        snapshot_path=FIXTURES / "python_etl",
    )

    learner_dir = get_workspace_dir(project_id, ws_id)
    ref_dir = get_reference_dir(project_id, artifact.id)
    hidden_dir = get_hidden_dir(project_id, artifact.id)

    # 1. Learner dir contains starter with NotImplementedError
    starter_path = learner_dir / "src/orders/normalize.py"
    assert starter_path.exists()
    assert "raise NotImplementedError" in starter_path.read_text()
    assert "TODO" in starter_path.read_text()

    # 2. Learner dir does NOT contain hidden test file
    assert not (learner_dir / "tests/test_hidden_edge_cases.py").exists()

    # 3. Hidden dir contains hidden test
    assert (hidden_dir / "tests/test_hidden_edge_cases.py").exists()

    # 4. Reference dir contains the original implementation
    ref_norm = ref_dir / "src/orders/normalize.py"
    assert ref_norm.exists()
    assert "ORDER_SCHEMA" in ref_norm.read_text()
    assert "dropna" in ref_norm.read_text()
