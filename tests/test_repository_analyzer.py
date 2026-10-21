import tempfile
from pathlib import Path
from app.analysis import analyze_deterministic

FIXTURES = Path("/home/ranga/opencode/tutor/fixtures")


def test_python_etl_analysis():
    # Make sure python_etl has a test file to detect pytest adapter
    test_file = FIXTURES / "python_etl" / "tests" / "test_hello.py"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("def test_ok(): pass\n")

    res = analyze_deterministic(FIXTURES / "python_etl")
    assert "Python" in res["stack"]
    assert "pytest" in res["stack"]
    assert "python_pytest" in res["detected_adapters"]

    paths = [item["path"] for item in res["inventory"]]
    assert "src/hello.py" in paths
    assert "README.md" in paths


def test_duckdb_pipeline_analysis():
    res = analyze_deterministic(FIXTURES / "duckdb_pipeline")
    assert "SQL" in res["stack"]
    assert "sql_duckdb" in res["detected_adapters"]

    paths = [item["path"] for item in res["inventory"]]
    assert "sql/orders.sql" in paths
    assert "sql/normalize.sql" in paths


def test_secrets_not_selected_in_excerpts():
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp)
        (p / "README.md").write_text("# Project")
        (p / ".env").write_text("SECRET_KEY=supersecret")
        (p / ".env.local").write_text("API_KEY=12345")
        (p / "id_rsa").write_text("PRIVATE KEY")
        (p / "credentials.json").write_text('{"token": "xyz"}')
        (p / "server.pem").write_text("CERT")
        (p / "main.py").write_text("print('hello')")

        res = analyze_deterministic(p)
        excerpt_paths = [e["path"] for e in res["excerpts"]]

        assert "README.md" in excerpt_paths
        assert "main.py" in excerpt_paths
        assert ".env" not in excerpt_paths
        assert ".env.local" not in excerpt_paths
        assert "id_rsa" not in excerpt_paths
        assert "credentials.json" not in excerpt_paths
        assert "server.pem" not in excerpt_paths
