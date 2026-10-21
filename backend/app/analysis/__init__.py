from pathlib import Path
from app.analysis.inventory import build_inventory
from app.analysis.select import select_excerpts
from app.analysis.stack import detect_stack_and_adapters


def analyze_deterministic(snapshot: Path) -> dict:
    inventory = build_inventory(snapshot)
    stack, detected_adapters = detect_stack_and_adapters(snapshot, inventory)
    excerpts = select_excerpts(snapshot, inventory, max_chars=80_000)

    return {
        "inventory": inventory,
        "stack": stack,
        "detected_adapters": detected_adapters,
        "excerpts": excerpts,
    }
