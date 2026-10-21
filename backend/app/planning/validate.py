import re
from typing import Set
from app.schemas import LearningPlan

ID_PATTERN = re.compile(r"^DE-\d{3}$")
VALID_ADAPTERS = {"python_pytest", "sql_duckdb", "dbt", "pyspark", "plan_only"}


def validate_learning_plan(
    plan: LearningPlan,
    valid_paths: Set[str] | None = None,
    detected_adapters: list[str] | None = None,
) -> tuple[bool, str, LearningPlan]:
    seen_ids = set()
    id_map = {}

    # Check IDs and regex
    for a in plan.assignments:
        if not ID_PATTERN.match(a.id):
            return False, f"Assignment ID '{a.id}' must match pattern DE-XXX (e.g. DE-001)", plan
        if a.id in seen_ids:
            return False, f"Duplicate assignment ID '{a.id}'", plan
        seen_ids.add(a.id)
        id_map[a.id] = a

    # Check prerequisites existence and build graph for cycle detection
    in_degree = {a_id: 0 for a_id in seen_ids}
    adj = {a_id: [] for a_id in seen_ids}

    for a in plan.assignments:
        for prereq in a.prerequisites:
            if prereq not in seen_ids:
                return False, f"Prerequisite '{prereq}' for assignment '{a.id}' does not exist in plan", plan
            adj[prereq].append(a.id)
            in_degree[a.id] += 1

    # Kahn's algorithm for cycle detection
    queue = [a_id for a_id, deg in in_degree.items() if deg == 0]
    visited_count = 0
    while queue:
        curr = queue.pop(0)
        visited_count += 1
        for neighbor in adj[curr]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if visited_count != len(seen_ids):
        return False, "Cycle detected in assignment prerequisites", plan

    # Check source_files against valid_paths
    if valid_paths is not None:
        for a in plan.assignments:
            for sf in a.source_files:
                if sf not in valid_paths:
                    return False, f"Source file '{sf}' in assignment '{a.id}' does not exist in repository inventory", plan

    # Check / coerce adapter
    det_set = set(detected_adapters or [])
    for a in plan.assignments:
        if a.adapter not in VALID_ADAPTERS:
            return False, f"Invalid adapter '{a.adapter}' in assignment '{a.id}'", plan
        if a.adapter != "plan_only" and detected_adapters is not None and a.adapter not in det_set:
            # Coerce to plan_only if adapter is not detected
            a.adapter = "plan_only"

    return True, "", plan
