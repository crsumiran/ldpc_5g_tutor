from typing import Any, Set
from app.db import SessionLocal
from app.models import Plan
from app.planning.validate import validate_learning_plan
from app.schemas import LearningPlan


def create_manual_plan(
    project_id: str,
    plan_data: dict[str, Any] | LearningPlan,
    valid_paths: Set[str] | None = None,
    detected_adapters: list[str] | None = None,
) -> Plan:
    if isinstance(plan_data, dict):
        plan_obj = LearningPlan.model_validate(plan_data)
    else:
        plan_obj = plan_data

    ok, err_msg, validated_plan = validate_learning_plan(
        plan_obj, valid_paths=valid_paths, detected_adapters=detected_adapters
    )
    if not ok:
        raise ValueError(f"Invalid manual plan: {err_msg}")

    db = SessionLocal()
    try:
        plan_row = Plan(
            project_id=project_id,
            json=validated_plan.model_dump_json(),
            status="draft",
        )
        db.add(plan_row)
        db.commit()
        db.refresh(plan_row)
        return plan_row
    finally:
        db.close()
