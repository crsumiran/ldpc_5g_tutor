from pathlib import Path

import pytest

from app.verilog.manifest import load_course, validate_manifest


def test_cache_lab_manifest_is_dependency_ordered():
    manifest, root = load_course("cache-lab")
    assert manifest.id == "cache-lab"
    assert len(manifest.checkpoints) == 6
    assert manifest.checkpoints[0].prerequisites == []
    assert manifest.checkpoints[-1].prerequisites == ["CACHE-05"]
    assert all(checkpoint.description and checkpoint.requirements for checkpoint in manifest.checkpoints)
    controller = manifest.checkpoints[4]
    assert any("mem_req_valid" in requirement and "stable" in requirement for requirement in controller.requirements)
    assert any("write miss" in requirement.lower() and "do not update" in requirement.lower() for requirement in controller.requirements)
    assert (root / "reference/rtl/simple_cache.v").is_file()


def test_manifest_rejects_unknown_prerequisite():
    manifest, root = load_course("cache-lab")
    broken = manifest.model_copy(deep=True)
    broken.checkpoints[1].prerequisites = ["CACHE-99"]
    with pytest.raises(ValueError, match="unknown prerequisite"):
        validate_manifest(broken, root)


def test_manifest_rejects_unsafe_path():
    manifest, root = load_course("cache-lab")
    broken = manifest.model_copy(deep=True)
    broken.checkpoints[0].source_files = ["../secret.v"]
    with pytest.raises(ValueError, match="unsafe curriculum path"):
        validate_manifest(broken, root)
