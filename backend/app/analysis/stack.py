from pathlib import Path


def detect_stack_and_adapters(snapshot: Path, inventory: list[dict]) -> tuple[list[str], list[str]]:
    paths = [item["path"] for item in inventory]
    stack: list[str] = []
    detected_adapters: list[str] = []

    has_py = any(p.endswith(".py") or p in ("pyproject.toml", "requirements.txt", "Pipfile", "setup.py") for p in paths)
    has_pytest = any("test" in p.lower() and p.endswith(".py") for p in paths)
    has_sql = any(p.endswith(".sql") for p in paths)
    has_dbt = any(p == "dbt_project.yml" or p.endswith("/dbt_project.yml") for p in paths)

    # Check file contents for library cues in requirements or manifests
    manifest_contents = ""
    for item in inventory:
        if item["path"] in ("requirements.txt", "pyproject.toml", "Pipfile", "setup.py"):
            try:
                manifest_contents += (snapshot / item["path"]).read_text(encoding="utf-8", errors="ignore").lower() + "\n"
            except Exception:
                pass

    if has_py:
        if "Python" not in stack:
            stack.append("Python")
    if "pytest" in manifest_contents or has_pytest:
        if "pytest" not in stack:
            stack.append("pytest")
    if has_sql or "duckdb" in manifest_contents:
        if "SQL" not in stack:
            stack.append("SQL")
    if "duckdb" in manifest_contents or any("duckdb" in p.lower() for p in paths):
        if "DuckDB" not in stack:
            stack.append("DuckDB")
    if has_dbt:
        if "dbt" not in stack:
            stack.append("dbt")
    if "pyspark" in manifest_contents or any("spark" in p.lower() for p in paths):
        if "PySpark" not in stack:
            stack.append("PySpark")
    if "airflow" in manifest_contents or any("airflow" in p.lower() for p in paths):
        if "Airflow" not in stack:
            stack.append("Airflow")
    if "dagster" in manifest_contents or any("dagster" in p.lower() for p in paths):
        if "Dagster" not in stack:
            stack.append("Dagster")
    if "prefect" in manifest_contents or any("prefect" in p.lower() for p in paths):
        if "Prefect" not in stack:
            stack.append("Prefect")

    # Adapters
    if has_pytest or ("pytest" in stack and has_py):
        detected_adapters.append("python_pytest")
    if has_sql and not has_dbt:
        detected_adapters.append("sql_duckdb")
    if has_dbt:
        detected_adapters.append("dbt")
    if "PySpark" in stack:
        detected_adapters.append("pyspark")

    return stack, detected_adapters
