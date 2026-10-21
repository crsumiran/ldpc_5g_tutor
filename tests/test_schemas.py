import pytest
from pydantic import ValidationError
from app.schemas import (
    AssignmentArtifact,
    Evaluation,
    FileBlob,
    LearningPlan,
    PlanAssignment,
    RepositoryAnalysis,
    RubricItem,
)


def test_learning_plan_valid():
    data = {
        "title": "Data Engineering 101",
        "learner_level": "python_comfortable",
        "status": "draft",
        "assignments": [
            {
                "id": "DE-001",
                "title": "Validate raw order records",
                "prerequisites": [],
                "concepts": ["schema validation", "null handling"],
                "source_files": ["src/orders/validation.py"],
                "estimated_minutes": 45,
                "difficulty": "medium",
                "adapter": "python_pytest",
            }
        ],
    }
    plan = LearningPlan.model_validate(data)
    assert plan.title == "Data Engineering 101"
    assert len(plan.assignments) == 1
    assert plan.assignments[0].id == "DE-001"


def test_learning_plan_missing_title():
    data = {
        "learner_level": "python_comfortable",
        "status": "draft",
        "assignments": [],
    }
    with pytest.raises(ValidationError):
        LearningPlan.model_validate(data)


def test_learning_plan_extra_fields_forbidden():
    data = {
        "title": "Test Plan",
        "learner_level": "python_comfortable",
        "status": "draft",
        "assignments": [],
        "extra_field": "disallowed",
    }
    with pytest.raises(ValidationError):
        LearningPlan.model_validate(data)


def test_repository_analysis_valid():
    data = {
        "project_summary": "ETL pipeline",
        "stack": ["Python", "pytest"],
        "components": [
            {
                "name": "Validation",
                "kind": "pipeline",
                "paths": ["src/orders/validation.py"],
                "summary": "Validates orders",
            }
        ],
        "data_flows": [
            {
                "source": "raw_orders",
                "sink": "clean_orders",
                "paths": ["src/pipeline.py"],
                "summary": "cleans data",
            }
        ],
        "development_commands": [{"name": "test", "command": ["pytest", "-q"]}],
        "important_files": [{"path": "src/orders/validation.py", "reason": "core transform", "bytes": 1200}],
        "detected_adapters": ["python_pytest"],
        "risks": [],
        "unknowns": [],
    }
    analysis = RepositoryAnalysis.model_validate(data)
    assert analysis.project_summary == "ETL pipeline"
    assert analysis.detected_adapters == ["python_pytest"]


def test_assignment_artifact_valid():
    data = {
        "id": "DE-001",
        "title": "Normalize Orders",
        "business_context": "Canonical schemas",
        "objectives": ["Implement normalize_orders"],
        "concepts": ["pandas", "datetime"],
        "inspect_files": ["src/orders/normalize.py"],
        "task": "Implement data normalization",
        "approach": ["Step 1: Copy dataframe", "Step 2: Parse timestamps"],
        "starter_files": [{"path": "src/orders/normalize.py", "content": "def normalize_orders(): pass"}],
        "public_tests": [{"path": "tests/test_normalize.py", "content": "def test_ok(): pass"}],
        "hidden_tests": [{"path": "hidden/test_hidden.py", "content": "def test_hidden(): pass"}],
        "run_command": ["pytest", "tests/test_normalize.py", "-q"],
        "hints": ["Check datetime formats", "Use pd.to_datetime", "utc=True"],
        "rubric": [{"name": "correctness", "weight": 0.7}, {"name": "cleanliness", "weight": 0.3}],
        "acceptance": ["public tests pass"],
        "estimated_minutes": 45,
        "adapter": "python_pytest",
    }
    artifact = AssignmentArtifact.model_validate(data)
    assert artifact.id == "DE-001"
    assert artifact.adapter == "python_pytest"


def test_evaluation_valid():
    data = {
        "setup_ok": True,
        "syntax_ok": True,
        "public": {"passed": 3, "failed": 1, "errors": 0, "output": "FAIL"},
        "hidden": {"passed": 0, "failed": 2, "errors": 0, "output": "FAIL"},
        "lint": {"ok": True, "output": ""},
        "timed_out": False,
        "runtime_ms": 812,
        "passed": False,
        "rubric_scores": {"correctness": 0.4, "cleanliness": 0.8},
    }
    ev = Evaluation.model_validate(data)
    assert not ev.passed
    assert ev.public.passed == 3
