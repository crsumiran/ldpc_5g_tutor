import json
from pathlib import Path
from typing import Set

from app.config import settings
from app.llm import complete_json
from app.planning.validate import validate_learning_plan
from app.schemas import LearningPlan, RepositoryAnalysis

PROMPT_FILE = Path("/home/ranga/opencode/tutor/backend/prompts/planner.txt")


def generate_plan_with_llm(
    analysis: RepositoryAnalysis,
    valid_paths: Set[str] | None = None,
    notes: str | None = None,
    model: str | None = None,
) -> LearningPlan:
    system_prompt = PROMPT_FILE.read_text(encoding="utf-8")
    user_payload = {
        "analysis": analysis.model_dump(),
        "mentor_notes": notes or "",
    }

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Generate a learning plan for this repository analysis:\n\n{json.dumps(user_payload, indent=2)}"},
    ]

    raw_json = complete_json(messages, model=model or settings.planner_model)
    try:
        plan = LearningPlan.model_validate(raw_json)
        ok, err_msg, validated_plan = validate_learning_plan(
            plan, valid_paths=valid_paths, detected_adapters=analysis.detected_adapters
        )
        if ok:
            return validated_plan
    except Exception as e:
        err_msg = str(e)

    # Retry once with feedback
    retry_messages = list(messages) + [
        {"role": "assistant", "content": json.dumps(raw_json)},
        {"role": "user", "content": f"The generated plan had validation errors:\n{err_msg}\nPlease fix all errors and return valid LearningPlan JSON."},
    ]
    raw_json2 = complete_json(retry_messages, model=model or settings.planner_model)
    plan2 = LearningPlan.model_validate(raw_json2)
    ok2, err_msg2, validated_plan2 = validate_learning_plan(
        plan2, valid_paths=valid_paths, detected_adapters=analysis.detected_adapters
    )
    if not ok2:
        raise ValueError(f"Plan validation failed after retry: {err_msg2}")

    return validated_plan2
