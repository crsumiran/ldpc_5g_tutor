from pathlib import Path
import shutil

from app.assignments.workspace import (
    get_reference_dir,
    get_workspace_dir,
    materialize_workspace,
)
from app.eval.evaluate import evaluate_submission
from app.schemas import AssignmentArtifact, FileBlob

FIXTURES = Path("/home/ranga/opencode/tutor/fixtures")


def test_evaluator_starter_fails_and_reference_passes():
    project_id = "test-proj-eval"
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
                content="import pandas as pd\n\nORDER_SCHEMA = ['order_id', 'ts_utc', 'amount']\n\ndef normalize_orders(df):\n    # TODO: implement\n    raise NotImplementedError\n",
            )
        ],
        public_tests=[
            FileBlob(
                path="tests/test_normalize.py",
                content="""import pandas as pd
from src.orders.normalize import normalize_orders, ORDER_SCHEMA

def test_normalize():
    df = pd.DataFrame({
        'order_id': ['O1', 'O2'],
        'order_date': ['2026-01-01', '2026-01-02'],
        'amount': [100.0, 200.0]
    })
    res = normalize_orders(df)
    assert list(res.columns) == ORDER_SCHEMA
    assert len(res) == 2
""",
            )
        ],
        hidden_tests=[],
        run_command=["pytest", "tests/test_normalize.py", "-v"],
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

    # 1. Starter code should fail evaluation
    ev1 = evaluate_submission(
        project_id=project_id,
        workspace_path=learner_dir,
        assignment=artifact,
    )
    assert not ev1.passed
    assert ev1.public.failed > 0 or ev1.public.errors > 0

    # 2. Copy correct reference code into learner workspace
    ref_dir = get_reference_dir(project_id, artifact.id)
    shutil.copy2(ref_dir / "src/orders/normalize.py", learner_dir / "src/orders/normalize.py")

    # 3. Now evaluation must pass
    ev2 = evaluate_submission(
        project_id=project_id,
        workspace_path=learner_dir,
        assignment=artifact,
    )
    assert ev2.passed
    assert ev2.public.passed >= 1
