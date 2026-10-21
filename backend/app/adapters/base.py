from pathlib import Path
from typing import Protocol
from app.schemas import AssignmentArtifact


class ProjectAdapter(Protocol):
    name: str

    def detect(self, snapshot: Path) -> bool:
        ...

    def test_command(self, assignment: AssignmentArtifact) -> list[str]:
        ...

    def evaluate_in_container_args(self, assignment: AssignmentArtifact) -> list[str]:
        ...
