from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.analysis.llm_analyze import analyze_with_llm
from app.main import app

FIXTURES = Path("/home/ranga/opencode/tutor/fixtures")
client = TestClient(app)


def test_health_endpoint():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_llm_analysis_strips_invented_paths():
    fake_llm_response = {
        "project_summary": "Test ETL Pipeline",
        "stack": ["Python", "pytest"],
        "components": [
            {
                "name": "HelloModule",
                "kind": "pipeline",
                "paths": ["src/hello.py", "non_existent/fake.py"],
                "summary": "Greets ETL",
            }
        ],
        "data_flows": [
            {
                "source": "raw",
                "sink": "clean",
                "paths": ["src/hello.py", "invalid/flow.py"],
                "summary": "Flow",
            }
        ],
        "development_commands": [{"name": "test", "command": ["pytest", "-q"]}],
        "important_files": [
            {"path": "src/hello.py", "reason": "greeting", "bytes": 50},
            {"path": "invented/ghost.py", "reason": "fake file", "bytes": 999},
        ],
        "detected_adapters": ["python_pytest", "unknown_adapter"],
        "risks": [],
        "unknowns": [],
    }

    with patch("app.analysis.llm_analyze.complete_json", return_value=fake_llm_response):
        analysis = analyze_with_llm(FIXTURES / "python_etl")

        # The ghost file must be stripped from important_files
        paths = [f.path for f in analysis.important_files]
        assert "src/hello.py" in paths
        assert "invented/ghost.py" not in paths

        # The non-existent paths must be stripped from component paths
        assert "src/hello.py" in analysis.components[0].paths
        assert "non_existent/fake.py" not in analysis.components[0].paths

        # The unknown adapter must be removed
        assert "python_pytest" in analysis.detected_adapters
        assert "unknown_adapter" not in analysis.detected_adapters
