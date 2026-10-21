"""Small, public-run-only VCD summary for tutor timing explanations."""

import re
from pathlib import Path


_SIGNALS = {"cpu_resp_valid", "cpu_resp_rdata", "cpu_resp_hit", "mem_resp_valid", "mem_resp_rdata"}
_UNIT_TO_NS = {"s": 1e9, "ms": 1e6, "us": 1e3, "ns": 1.0, "ps": 1e-3, "fs": 1e-6}


def _hex_value(bits: str | None) -> str:
    if not bits or any(char not in "01" for char in bits.lower()):
        return bits or "unknown"
    return f"0x{int(bits, 2):08x}"


def response_pulses(path: Path, max_bytes: int = 256 * 1024) -> list[dict[str, str]]:
    """Return bounded response-valid windows, not a raw waveform or hidden signals."""
    if not path.is_file() or path.stat().st_size > max_bytes:
        return []
    content = path.read_text(encoding="utf-8", errors="replace")
    scale = re.search(r"\$timescale\s+(\d+)\s*(s|ms|us|ns|ps|fs)\s+\$end", content)
    ns_per_tick = int(scale.group(1)) * _UNIT_TO_NS[scale.group(2)] if scale else 1.0
    scope: list[str] = []
    symbol_to_name: dict[str, str] = {}
    values: dict[str, str] = {}
    pulses: list[dict[str, str]] = []
    previous_valid = "0"
    active: dict[str, str] | None = None
    current_time: int | None = None
    header = True

    def flush() -> None:
        nonlocal previous_valid, active
        if current_time is None:
            return
        valid = values.get("cpu_resp_valid", "0")
        time_ns = f"{current_time * ns_per_tick:g} ns"
        if valid == "1" and previous_valid != "1" and len(pulses) < 8:
            active = {
                "start": time_ns,
                "data": _hex_value(values.get("cpu_resp_rdata")),
                "hit": values.get("cpu_resp_hit", "unknown"),
                "memory_data": _hex_value(values.get("mem_resp_rdata")),
            }
            pulses.append(active)
        elif valid != "1" and previous_valid == "1" and active is not None:
            active["end"] = time_ns
            active["data_after"] = _hex_value(values.get("cpu_resp_rdata"))
            active = None
        previous_valid = valid

    for raw in content.splitlines():
        line = raw.strip()
        if header:
            if line.startswith("$scope "):
                scope.append(line.split()[2])
            elif line.startswith("$upscope"):
                if scope:
                    scope.pop()
            elif line.startswith("$var ") and len(scope) == 1:
                fields = line.split()
                if len(fields) >= 5 and fields[4] in _SIGNALS:
                    symbol_to_name[fields[3]] = fields[4]
            elif line == "$enddefinitions $end":
                header = False
            continue
        if line.startswith("#") and line[1:].isdigit():
            flush()
            current_time = int(line[1:])
        elif line.startswith("b"):
            parts = line[1:].split()
            if len(parts) == 2 and parts[1] in symbol_to_name:
                values[symbol_to_name[parts[1]]] = parts[0]
        elif len(line) >= 2 and line[0] in "01xXzZ" and line[1:] in symbol_to_name:
            values[symbol_to_name[line[1:]]] = line[0].lower()
    flush()
    return pulses
