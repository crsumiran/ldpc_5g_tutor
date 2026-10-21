from pathlib import Path

import pytest

from app.verilog.manifest import load_course
from app.verilog.workspace import (
    allowed_editable_files,
    materialize_lab_workspace,
    read_workspace_file,
    write_workspace_file,
)


def test_lab_workspace_contains_sources_and_provided_files():
    manifest, root = load_course("cache-lab")
    _, workspace = materialize_lab_workspace(root, manifest, "workspace-unit-test")
    assert (workspace / "rtl/cache_address_decode.v").is_file()
    assert (workspace / "provided/rtl/backing_memory.v").is_file()
    assert "rtl/cache_address_decode.v" in allowed_editable_files(manifest, set(), "CACHE-01")
    assert "rtl/cache_tag_array.v" not in allowed_editable_files(manifest, set(), "CACHE-01")


def test_workspace_rejects_traversal_and_large_files(tmp_path):
    with pytest.raises(ValueError):
        write_workspace_file(tmp_path, "../outside.v", "module x; endmodule")
    with pytest.raises(ValueError):
        write_workspace_file(tmp_path, "rtl/x.v", "x" * (256 * 1024 + 1))
