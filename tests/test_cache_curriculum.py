import shutil
from pathlib import Path

import pytest

from app.verilog.manifest import load_course
from app.verilog.runner import run_checkpoint
from app.verilog.workspace import materialize_lab_workspace


def test_cache_starter_fails_and_reference_passes(tmp_path):
    manifest, course_root = load_course("cache-lab")
    starter_id, starter_workspace = materialize_lab_workspace(course_root, manifest, "cache-curriculum-starter")
    starter_result = run_checkpoint(course_root, starter_workspace, "CACHE-01", "test")
    assert starter_id == "cache-curriculum-starter"
    assert starter_result.compile.ok
    assert not starter_result.passed

    reference_workspace = tmp_path / "reference-workspace"
    shutil.copytree(course_root / "starter", reference_workspace)
    for checkpoint in manifest.checkpoints:
        for relative in checkpoint.source_files:
            reference_path = course_root / "reference" / relative
            destination = reference_workspace / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(reference_path, destination)
    reference_result = run_checkpoint(course_root, reference_workspace, "CACHE-01", "submit")
    assert reference_result.passed
    assert reference_result.hidden is not None
    assert reference_result.hidden.failed == 0
    assert reference_result.hidden.cases == []


@pytest.mark.parametrize("checkpoint_id", [f"CACHE-{index:02d}" for index in range(1, 7)])
def test_cache_reference_passes_every_checkpoint(tmp_path, checkpoint_id):
    manifest, course_root = load_course("cache-lab")
    reference_workspace = tmp_path / checkpoint_id
    shutil.copytree(course_root / "starter", reference_workspace)
    for checkpoint in manifest.checkpoints:
        for relative in checkpoint.source_files:
            reference_path = course_root / "reference" / relative
            destination = reference_workspace / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(reference_path, destination)

    result = run_checkpoint(course_root, reference_workspace, checkpoint_id, "submit")

    assert result.passed, result.output
    assert result.hidden is not None
    assert result.hidden.failed == 0
    assert result.hidden.errors == 0
