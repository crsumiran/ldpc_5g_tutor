from pathlib import Path
from app.adapters import get_adapter
from app.adapters.python_pytest import PythonPytestAdapter
from app.adapters.sql_duckdb import SqlDuckDBAdapter
from app.schemas import AssignmentArtifact

FIXTURES = Path("/home/ranga/opencode/tutor/fixtures")


def test_python_pytest_adapter():
    adapter = get_adapter("python_pytest")
    assert adapter is not None
    assert isinstance(adapter, PythonPytestAdapter)

    # Detect on python_etl -> True
    assert adapter.detect(FIXTURES / "python_etl") is True

    # Detect on duckdb_pipeline -> False
    assert adapter.detect(FIXTURES / "duckdb_pipeline") is False

    # Test command
    artifact = AssignmentArtifact(
        id="DE-001",
        title="T",
        business_context="C",
        objectives=[],
        concepts=[],
        inspect_files=[],
        task="T",
        approach=[],
        starter_files=[],
        public_tests=[],
        hidden_tests=[],
        run_command=["pytest", "tests/test_normalize.py", "-q"],
        hints=[],
        rubric=[],
        acceptance=[],
        estimated_minutes=30,
        adapter="python_pytest",
    )
    cmd = adapter.test_command(artifact)
    assert cmd == ["pytest", "tests/test_normalize.py", "-q"]


def test_sql_duckdb_adapter():
    adapter = get_adapter("sql_duckdb")
    assert adapter is not None
    assert isinstance(adapter, SqlDuckDBAdapter)

    # Detect on duckdb_pipeline -> True
    assert adapter.detect(FIXTURES / "duckdb_pipeline") is True

    # Detect on python_etl -> False
    assert adapter.detect(FIXTURES / "python_etl") is False
