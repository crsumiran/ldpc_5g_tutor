import json
from pathlib import Path
from typing import Any

from app.analysis import analyze_deterministic
from app.config import settings
from app.db import SessionLocal
from app.llm import complete_json
from app.models import Analysis
from app.schemas import RepositoryAnalysis

PROMPT_FILE = Path("/home/ranga/opencode/tutor/backend/prompts/analyst.txt")
ALLOWED_ADAPTERS = {"python_pytest", "sql_duckdb", "dbt", "pyspark"}


def sanitize_llm_analysis(raw_data: dict[str, Any], inventory_paths: set[str], fallback_adapters: list[str]) -> dict[str, Any]:
    cleaned = dict(raw_data)

    # Filter components
    if "components" in cleaned and isinstance(cleaned["components"], list):
        valid_components = []
        for comp in cleaned["components"]:
            if isinstance(comp, dict):
                comp_paths = [p for p in comp.get("paths", []) if p in inventory_paths]
                comp["paths"] = comp_paths
                valid_components.append(comp)
        cleaned["components"] = valid_components

    # Filter data flows
    if "data_flows" in cleaned and isinstance(cleaned["data_flows"], list):
        valid_flows = []
        for flow in cleaned["data_flows"]:
            if isinstance(flow, dict):
                flow_paths = [p for p in flow.get("paths", []) if p in inventory_paths]
                flow["paths"] = flow_paths
                valid_flows.append(flow)
        cleaned["data_flows"] = valid_flows

    # Filter important files: drop any that don't exist in inventory
    if "important_files" in cleaned and isinstance(cleaned["important_files"], list):
        cleaned["important_files"] = [
            f for f in cleaned["important_files"]
            if isinstance(f, dict) and f.get("path") in inventory_paths
        ]

    # Validate detected adapters
    raw_adapters = cleaned.get("detected_adapters", [])
    valid_adapters = [a for a in raw_adapters if a in ALLOWED_ADAPTERS]
    if not valid_adapters:
        valid_adapters = fallback_adapters
    cleaned["detected_adapters"] = valid_adapters

    return cleaned


def analyze_with_llm(snapshot: Path, project_id: str | None = None, model: str | None = None) -> RepositoryAnalysis:
    det_res = analyze_deterministic(snapshot)
    inventory_paths = {item["path"] for item in det_res["inventory"]}

    system_prompt = PROMPT_FILE.read_text(encoding="utf-8")
    user_payload = {
        "inventory": [item["path"] for item in det_res["inventory"]],
        "deterministic_stack": det_res["stack"],
        "deterministic_adapters": det_res["detected_adapters"],
        "excerpts": det_res["excerpts"],
    }

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Analyze this project repository:\n\n{json.dumps(user_payload, indent=2)}"},
    ]

    raw_json = complete_json(messages, model=model or settings.planner_model)
    cleaned_data = sanitize_llm_analysis(raw_json, inventory_paths, det_res["detected_adapters"])
    analysis_obj = RepositoryAnalysis.model_validate(cleaned_data)

    if project_id:
        db = SessionLocal()
        try:
            analysis_row = Analysis(
                project_id=project_id,
                json=analysis_obj.model_dump_json(),
            )
            db.add(analysis_row)
            db.commit()
        finally:
            db.close()

    return analysis_obj
