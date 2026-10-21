"""Author-only: record public expected results from independently tested baselines.

Prints JSON to stdout. Does not edit learner files or distribute implementations.
Run with PYTHONPATH=backend .venv/bin/python scripts/export_ldpc_public_cases.py.
"""
import contextlib
import functools
import importlib.util
import io
import json
import sys
import types
from pathlib import Path

import numpy as np

from app.verilog.manifest import load_course


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def encode(value):
    if isinstance(value, np.ndarray):
        return {"type": "array", "shape": list(value.shape), "values": value.tolist()}
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {key: encode(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [encode(item) for item in value]
    return value


def main():
    repo = Path(__file__).resolve().parents[1]
    author = load_module("author_baselines", repo / "tests/test_ldpc_course.py")
    manifest, root = load_course("ldpc-5g")
    functions = author.baseline_modules()
    # Resolve imported dependencies exactly as the author regression does.
    for checkpoint in manifest.checkpoints:
        module = types.ModuleType(checkpoint.module)
        starter = (root / "starter" / checkpoint.editable_files[0]).read_text()
        function = next(fn for name, fn in functions.items()
                        if callable(fn) and f"def {name}(" in starter)
        setattr(module, function.__name__, function)
        sys.modules[checkpoint.module] = module
    provided = types.ModuleType("provided")
    provided.__path__ = [str(root / "python/provided")]
    sys.modules["provided"] = provided
    result = {}
    for checkpoint in manifest.checkpoints:
        suite = load_module("public_suite", root / checkpoint.public_testbench)
        module = sys.modules[checkpoint.module]
        name, function = next((name, fn) for name, fn in vars(module).items() if callable(fn))
        cases = {}
        for case_name, case in list(vars(suite).items()):
            if not case_name.startswith("test_"):
                continue
            calls = []

            @functools.wraps(function)
            def record(*args, **kwargs):
                try:
                    value = function(*args, **kwargs)
                except ValueError:
                    calls.append({"raises": "ValueError"})
                    raise
                calls.append({"result": encode(value)})
                return value

            setattr(suite, name, record)
            with contextlib.redirect_stdout(io.StringIO()):
                case()
            cases[case_name] = calls
        result[checkpoint.id] = {"function": name, "cases": cases}
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
