import os
from pathlib import Path
from app.schemas import AssignmentArtifact


class SqlDuckDBAdapter:
    name: str = "sql_duckdb"

    def detect(self, snapshot: Path) -> bool:
        has_sql = False
        has_dbt = (snapshot / "dbt_project.yml").exists()
        for root, _, files in os.walk(snapshot):
            for f in files:
                if f.endswith(".sql"):
                    has_sql = True
                if f == "dbt_project.yml":
                    has_dbt = True
        return has_sql and not has_dbt

    def test_command(self, assignment: AssignmentArtifact) -> list[str]:
        if assignment.run_command:
            return assignment.run_command
        return ["duckdb", ":memory:"]

    def evaluate_in_container_args(self, assignment: AssignmentArtifact) -> list[str]:
        script = """
set -e
echo "=== DUCKDB EVALUATION ==="
python3 -c "
import duckdb, glob, os
con = duckdb.connect(':memory:')
for sql_file in sorted(glob.glob('**/*.sql', recursive=True)):
    with open(sql_file) as f:
        con.execute(f.read())
print('ALL_TESTS_PASSED')
"
"""
        return ["bash", "-c", script]
