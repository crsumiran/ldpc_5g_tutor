import re
from pathlib import Path

SECRET_PATTERN = re.compile(
    r"(^\.env(\..*)?$|^id_rsa$|^.*\.pem$|^credentials\.json$)",
    re.IGNORECASE,
)


def is_secret_file(path_str: str) -> bool:
    name = Path(path_str).name
    if SECRET_PATTERN.match(name):
        return True
    if ".env" in name:
        return True
    return False


def get_file_priority(path_str: str) -> int:
    name = Path(path_str).name.lower()
    p_lower = path_str.lower()

    if name.startswith("readme"):
        return 1
    if name in ("requirements.txt", "pyproject.toml", "dbt_project.yml", "pipfile", "setup.py"):
        return 2
    if (p_lower.startswith("src/") or p_lower.startswith("app/") or p_lower.startswith("models/") or p_lower.startswith("sql/")) and (name.endswith(".py") or name.endswith(".sql")):
        return 3
    if "test" in p_lower and (name.endswith(".py") or name.endswith(".sql")):
        return 4
    if name.endswith(".py") or name.endswith(".sql") or name.endswith(".md") or name.endswith(".json") or name.endswith(".yaml") or name.endswith(".yml"):
        return 5
    return 6


def select_excerpts(
    snapshot: Path,
    inventory: list[dict],
    max_chars: int = 80_000,
) -> list[dict]:
    # Filter candidate text files
    candidates = [
        item for item in inventory
        if item.get("can_excerpt") and not is_secret_file(item["path"])
    ]

    # Sort by priority then by path
    candidates.sort(key=lambda item: (get_file_priority(item["path"]), item["path"]))

    selected: list[dict] = []
    current_chars = 0

    for item in candidates:
        if current_chars >= max_chars:
            break

        file_path = snapshot / item["path"]
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        remaining_budget = max_chars - current_chars
        if len(content) > remaining_budget:
            content = content[:remaining_budget] + "\n... [truncated]"

        selected.append({
            "path": item["path"],
            "content": content,
            "bytes": len(content.encode("utf-8")),
        })
        current_chars += len(content)

    return selected
