"""Public trace only: assertions in the original suite still determine grades."""
import functools
import inspect
import json
from pathlib import Path

import numpy as np
import pytest


def describe(value):
    if isinstance(value, np.ndarray):
        return {"type": "array", "shape": list(value.shape), "dtype": str(value.dtype), "values": value.tolist()}
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, dict):
        return {key: describe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [describe(item) for item in value]
    return value


@pytest.fixture(autouse=True)
def print_public_case(request, monkeypatch):
    spec = json.loads(Path(__file__).with_name("teaching_case.json").read_text())
    expected_calls = spec["cases"][request.node.originalname or request.node.name]
    function = getattr(request.module, spec["function"])
    index = 0

    @functools.wraps(function)
    def traced(*args, **kwargs):
        nonlocal index
        expected = expected_calls[index]
        index += 1
        print(f"\n--- {request.node.name} / {spec['function']} / call {index} ---", flush=True)
        bound = inspect.signature(function).bind(*args, **kwargs)
        print("INPUT: " + json.dumps(describe(dict(bound.arguments)), allow_nan=True), flush=True)
        print("EXPECTED OUTPUT: " + json.dumps(expected, allow_nan=True), flush=True)
        try:
            actual = function(*args, **kwargs)
        except Exception as error:
            # Report the exception but retain pytest's original failure handling.
            print("ACTUAL OUTPUT: " + json.dumps({"raises": type(error).__name__, "message": str(error)[:1000]}), flush=True)
            raise
        print("ACTUAL OUTPUT: " + json.dumps(describe(actual), allow_nan=True), flush=True)
        return actual

    monkeypatch.setattr(request.module, spec["function"], traced)
    yield
