import os
from pathlib import Path
from app.schemas import AssignmentArtifact


class PythonPytestAdapter:
    name: str = "python_pytest"

    def detect(self, snapshot: Path) -> bool:
        if (snapshot / "tests").is_dir():
            return True
        for root, _, files in os.walk(snapshot):
            for f in files:
                if f.startswith("test_") and f.endswith(".py"):
                    return True
                if f in ("requirements.txt", "pyproject.toml"):
                    try:
                        content = (Path(root) / f).read_text(encoding="utf-8", errors="ignore")
                        if "pytest" in content:
                            return True
                    except Exception:
                        pass
        return False

    def test_command(self, assignment: AssignmentArtifact) -> list[str]:
        if assignment.run_command:
            return assignment.run_command
        return ["pytest", "-q"]

    def evaluate_in_container_args(self, assignment: AssignmentArtifact) -> list[str]:
        script = """
set -e
echo "=== PUBLIC TESTS ==="
python3 -m pytest -v
if [ -d /hidden ] && [ "$(ls -A /hidden 2>/dev/null)" ]; then
    echo "=== HIDDEN TESTS ==="
    cp -rn /hidden/* ./
    python3 -m pytest -v
fi
"""
        return ["bash", "-c", script]
