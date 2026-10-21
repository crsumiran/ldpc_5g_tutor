from app.adapters.base import ProjectAdapter
from app.adapters.python_pytest import PythonPytestAdapter
from app.adapters.sql_duckdb import SqlDuckDBAdapter

ADAPTERS: dict[str, ProjectAdapter] = {
    "python_pytest": PythonPytestAdapter(),
    "sql_duckdb": SqlDuckDBAdapter(),
}


def get_adapter(name: str) -> ProjectAdapter | None:
    return ADAPTERS.get(name)
