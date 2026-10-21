import os
from pathlib import Path


def is_binary_file(file_path: Path) -> bool:
    try:
        with open(file_path, "rb") as f:
            chunk = f.read(1024)
            if b"\x00" in chunk:
                return True
        return False
    except Exception:
        return True


def build_inventory(snapshot: Path) -> list[dict]:
    inventory: list[dict] = []
    for root, _, files in os.walk(snapshot):
        for f in files:
            fp = Path(root) / f
            try:
                rel = fp.relative_to(snapshot).as_posix()
                size = fp.stat().st_size
                is_bin = is_binary_file(fp)
                inventory.append({
                    "path": rel,
                    "bytes": size,
                    "suffix": fp.suffix.lower(),
                    "is_binary": is_bin,
                    "can_excerpt": not is_bin and size <= 256 * 1024,
                })
            except (OSError, PermissionError):
                continue

    # Sort deterministically by path
    inventory.sort(key=lambda item: item["path"])
    return inventory
