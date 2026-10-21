from unittest.mock import patch
import pytest

from app.planning.generate import generate_plan_with_llm
from app.planning.validate import validate_learning_plan
from app.schemas import LearningPlan, PlanAssignment, RepositoryAnalysis


def test_valid_linear_plan():
    plan = LearningPlan(
        title="Valid Plan",
        assignments=[
            PlanAssignment(id="DE-001", title="Step 1", prerequisites=[], source_files=["src/a.py"], adapter="python_pytest"),
            PlanAssignment(id="DE-002", title="Step 2", prerequisites=["DE-001"], source_files=["src/b.py"], adapter="python_pytest"),
        ],
    )
    valid_paths = {"src/a.py", "src/b.py"}
    ok, err, val_plan = validate_learning_plan(plan, valid_paths=valid_paths, detected_adapters=["python_pytest"])
    assert ok
    assert err == ""
    assert len(val_plan.assignments) == 2


def test_cycle_rejected():
    plan = LearningPlan(
        title="Cycle Plan",
        assignments=[
            PlanAssignment(id="DE-001", title="Step 1", prerequisites=["DE-002"], source_files=[]),
            PlanAssignment(id="DE-002", title="Step 2", prerequisites=["DE-001"], source_files=[]),
        ],
    )
    ok, err, _ = validate_learning_plan(plan)
    assert not ok
    assert "Cycle detected" in err


def test_unknown_file_rejected():
    plan = LearningPlan(
        title="Missing File Plan",
        assignments=[
            PlanAssignment(id="DE-001", title="Step 1", prerequisites=[], source_files=["nonexistent.py"]),
        ],
    )
    valid_paths = {"src/a.py"}
    ok, err, _ = validate_learning_plan(plan, valid_paths=valid_paths)
    assert not ok
    assert "does not exist in repository inventory" in err


def test_duplicate_ids_rejected():
    plan = LearningPlan(
        title="Duplicate Plan",
        assignments=[
            PlanAssignment(id="DE-001", title="Step 1", prerequisites=[]),
            PlanAssignment(id="DE-001", title="Step 1 duplicate", prerequisites=[]),
        ],
    )
    ok, err, _ = validate_learning_plan(plan)
    assert not ok
    assert "Duplicate assignment ID" in err


def test_pyspark_coerced_to_plan_only():
    fake_analysis = RepositoryAnalysis(
        project_summary="ETL project",
        stack=["Python", "pytest"],
        detected_adapters=["python_pytest"],
    )

    fake_plan_dict = {
        "title": "Generated Plan",
        "learner_level": "python_comfortable",
        "status": "draft",
        "assignments": [
            {
                "id": "DE-001",
                "title": "Spark Step",
                "prerequisites": [],
                "concepts": ["PySpark"],
                "source_files": ["src/hello.py"],
                "estimated_minutes": 45,
                "difficulty": "medium",
                "adapter": "pyspark",  # Not in detected_adapters!
            }
        ],
    }

    with patch("app.planning.generate.complete_json", return_value=fake_plan_dict):
        plan = generate_plan_with_llm(
            analysis=fake_analysis,
            valid_paths={"src/hello.py"},
        )
        assert plan.assignments[0].adapter == "plan_only"
