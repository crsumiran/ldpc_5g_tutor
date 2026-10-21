from pathlib import Path
from unittest.mock import patch
import pytest

from app.assignments.compile import compile_assignment
from app.schemas import FileBlob, PlanAssignment

FIXTURES = Path("/home/ranga/opencode/tutor/fixtures")


def test_compiler_rejects_missing_todo():
    fake_artifact = {
        "id": "DE-001",
        "title": "Task",
        "business_context": "Context",
        "objectives": ["Obj"],
        "concepts": ["Concept"],
        "inspect_files": ["src/hello.py"],
        "task": "Do task",
        "approach": ["Step 1"],
        "starter_files": [{"path": "src/hello.py", "content": "def hello(): pass\n"}],
        "public_tests": [{"path": "tests/test_hello.py", "content": "def test_hello(): pass\n"}],
        "hidden_tests": [],
        "run_command": ["pytest", "tests/test_hello.py"],
        "hints": ["hint 1", "hint 2", "hint 3"],
        "rubric": [{"name": "correctness", "weight": 1.0}],
        "acceptance": ["pass"],
        "estimated_minutes": 30,
        "adapter": "python_pytest",
    }

    plan_item = PlanAssignment(id="DE-001", title="Task", source_files=["src/hello.py"], adapter="python_pytest")

    with patch("app.assignments.compile.complete_json", return_value=fake_artifact):
        with pytest.raises(ValueError, match=r"TODO marker"):
            compile_assignment("plan-123", plan_item, FIXTURES / "python_etl")


def test_compiler_rejects_reference_leak():
    ref_code = """
def complex_algorithm(data):
    step1 = data.strip()
    step2 = step1.upper()
    step3 = step2.split(',')
    step4 = [x for x in step3 if x]
    return step4
"""
    # Write a fixture file with reference code
    ref_file = FIXTURES / "python_etl" / "src" / "complex.py"
    ref_file.write_text(ref_code)

    leaked_artifact = {
        "id": "DE-001",
        "title": "Task",
        "business_context": "Context",
        "objectives": ["Obj"],
        "concepts": ["Concept"],
        "inspect_files": ["src/complex.py"],
        "task": "Do task",
        "approach": ["Step 1"],
        "starter_files": [
            {
                "path": "src/complex.py",
                # Leaking the reference body directly!
                "content": "# TODO: implement\n" + ref_code,
            }
        ],
        "public_tests": [{"path": "tests/test_complex.py", "content": "def test_ok(): pass\n"}],
        "hidden_tests": [],
        "run_command": ["pytest", "tests/test_complex.py"],
        "hints": ["hint 1", "hint 2", "hint 3"],
        "rubric": [{"name": "correctness", "weight": 1.0}],
        "acceptance": ["pass"],
        "estimated_minutes": 30,
        "adapter": "python_pytest",
    }

    plan_item = PlanAssignment(id="DE-001", title="Task", source_files=["src/complex.py"], adapter="python_pytest")

    with patch("app.assignments.compile.complete_json", return_value=leaked_artifact):
        with pytest.raises(ValueError, match=r"Leak detected"):
            compile_assignment("plan-123", plan_item, FIXTURES / "python_etl")


def test_compiler_happy_path_accepted():
    valid_artifact = {
        "id": "DE-001",
        "title": "Task",
        "business_context": "Context",
        "objectives": ["Obj"],
        "concepts": ["Concept"],
        "inspect_files": ["src/hello.py"],
        "task": "Do task",
        "approach": ["Step 1", "Step 2"],
        "starter_files": [
            {
                "path": "src/hello.py",
                "content": "def hello():\n    # TODO: implement greeting\n    raise NotImplementedError\n",
            }
        ],
        "public_tests": [{"path": "tests/test_hello.py", "content": "def test_hello(): pass\n"}],
        "hidden_tests": [{"path": "hidden/test_secret.py", "content": "def test_secret(): pass\n"}],
        "run_command": ["pytest", "tests/test_hello.py", "-q"],
        "hints": ["Think about strings", "Return 'Hello ETL'", "Check casing"],
        "rubric": [{"name": "correctness", "weight": 1.0}],
        "acceptance": ["public tests pass", "hidden tests pass"],
        "estimated_minutes": 30,
        "adapter": "python_pytest",
    }

    plan_item = PlanAssignment(id="DE-001", title="Task", source_files=["src/hello.py"], adapter="python_pytest")

    with patch("app.assignments.compile.complete_json", return_value=valid_artifact):
        art = compile_assignment("plan-123", plan_item, FIXTURES / "python_etl")
        assert art.id == "DE-001"
        assert len(art.starter_files) == 1
        assert "NotImplementedError" in art.starter_files[0].content
