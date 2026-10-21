import json
import re
from pathlib import Path

from app.config import settings
from app.verilog.schemas import Checkpoint, CourseManifest


_SAFE_RELATIVE_PATH = re.compile(r"^[A-Za-z0-9_.][A-Za-z0-9_./-]*$")
_SAFE_ID = re.compile(r"^[A-Z]+-[0-9]{2,3}$")


def _validate_relative_path(root: Path, value: str) -> None:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or not _SAFE_RELATIVE_PATH.fullmatch(value):
        raise ValueError(f"unsafe curriculum path: {value}")
    if not (root / path).resolve().is_relative_to(root.resolve()):
        raise ValueError(f"curriculum path escapes course root: {value}")


def validate_manifest(manifest: CourseManifest, root: Path) -> CourseManifest:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,63}", manifest.id):
        raise ValueError("course id must contain lowercase letters, digits, and hyphens")
    checkpoint_ids = [checkpoint.id for checkpoint in manifest.checkpoints]
    if len(set(checkpoint_ids)) != len(checkpoint_ids):
        raise ValueError("checkpoint ids must be unique")

    known_ids: set[str] = set()
    editable_paths: set[str] = set()
    for checkpoint in manifest.checkpoints:
        if not _SAFE_ID.fullmatch(checkpoint.id):
            raise ValueError(f"invalid checkpoint id: {checkpoint.id}")
        missing_prerequisite_ids = [p for p in checkpoint.prerequisites if p not in known_ids]
        if missing_prerequisite_ids:
            raise ValueError(f"unknown prerequisite ids: {missing_prerequisite_ids}")
        if len(set(checkpoint.editable_files)) != len(checkpoint.editable_files):
            raise ValueError(f"editable files must be unique in {checkpoint.id}")
        for value in checkpoint.source_files + checkpoint.editable_files:
            _validate_relative_path(root, value)
            if not (root / "starter" / value).is_file() or (manifest.toolchain == "iverilog" and not (root / "reference" / value).is_file()):
                raise ValueError(f"starter/reference source file does not exist: {value}")
        if manifest.toolchain == "python" and checkpoint.expected_public_checks < 1:
            raise ValueError("Python checkpoints require a positive public check count")
        if manifest.toolchain == "iverilog" and not checkpoint.hidden_testbench:
            raise ValueError("Verilog checkpoints require a hidden testbench")
        for value in [checkpoint.public_testbench] + ([checkpoint.hidden_testbench] if checkpoint.hidden_testbench else []):
            _validate_relative_path(root, value)
            if not (root / value).is_file():
                raise ValueError(f"manifest file does not exist: {value}")
        if checkpoint.compile_testbench:
            _validate_relative_path(root, checkpoint.compile_testbench)
            if not (root / checkpoint.compile_testbench).is_file():
                raise ValueError(f"manifest file does not exist: {checkpoint.compile_testbench}")
        for path in checkpoint.editable_files:
            if path not in checkpoint.source_files:
                raise ValueError(f"editable path is not a source path in {checkpoint.id}: {path}")
            editable_paths.add(path)
        known_ids.add(checkpoint.id)

    for value in manifest.provided_files + [manifest.overview_file, manifest.architecture_file]:
        _validate_relative_path(root, value)
        if not (root / value).is_file():
            raise ValueError(f"manifest file does not exist: {value}")
    return manifest


def load_course(course_id: str, curriculum_dir: str | Path | None = None) -> tuple[CourseManifest, Path]:
    root = Path(curriculum_dir or settings.curriculum_dir) / course_id
    if not root.is_dir():
        root = Path(curriculum_dir or settings.curriculum_dir) / course_id.replace("-", "_")
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"unknown course: {course_id}")
    manifest = CourseManifest.model_validate(json.loads(manifest_path.read_text(encoding="utf-8")))
    if course_id == "ldpc-5g" and (root / "lesson_revisions.json").is_file():
        revisions = json.loads((root / "lesson_revisions.json").read_text(encoding="utf-8"))
        fixtures = json.loads((root / "fixtures.json").read_text(encoding="utf-8"))
        for i, checkpoint in enumerate(manifest.checkpoints):
            revision = dict(revisions.get(checkpoint.id, {}))
            fixture_id = revision.pop("fixture_id", None)
            if fixture_id:
                revision["fixture"] = fixtures[fixture_id]
            manifest.checkpoints[i] = Checkpoint.model_validate({**checkpoint.model_dump(), **revision})
    if manifest.id != course_id:
        raise ValueError(f"manifest id {manifest.id!r} does not match requested course {course_id!r}")
    return validate_manifest(manifest, root), root


def get_checkpoint(manifest: CourseManifest, checkpoint_id: str) -> Checkpoint:
    for checkpoint in manifest.checkpoints:
        if checkpoint.id == checkpoint_id:
            return checkpoint
    raise KeyError(f"unknown checkpoint: {checkpoint_id}")
