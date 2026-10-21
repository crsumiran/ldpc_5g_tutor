"""Trusted, authored introductory lessons, independent of learner progress."""
import json
from pathlib import Path

from app.verilog.schemas import TheoryPage


def load_theory(root: Path) -> list[TheoryPage]:
    pages = json.loads((root / "theory.json").read_text(encoding="utf-8"))
    fixtures = json.loads((root / "fixtures.json").read_text(encoding="utf-8")) if (root / "fixtures.json").is_file() else {}
    links = {"parity": "toy-encode", "sparse-graph": "toy-edges", "decoding": "flooding-chain"}
    for page in pages:
        if page["id"] in links and links[page["id"]] in fixtures:
            page["fixture"] = fixtures[links[page["id"]]]
    return [TheoryPage.model_validate(page) for page in pages]
