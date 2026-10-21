import hashlib
import os
import shlex
import shutil
import tempfile
import time
from pathlib import Path

from app.config import settings
from app.eval.sandbox import run_sandbox
from app.verilog.diagnostics import parse_diagnostics, parse_test_output, redact_hidden_output
from app.verilog.manifest import get_checkpoint, validate_manifest
from app.verilog.schemas import (
    Checkpoint,
    CompileSummary,
    Diagnostic,
    LabRunResult,
    RunArtifact,
    TestSummary,
)


MAX_OUTPUT = 128 * 1024


def source_hash(workspace: Path, paths: list[str]) -> str:
    _reject_workspace_symlinks(workspace)
    digest = hashlib.sha256()
    for relative in sorted(paths):
        path = workspace / relative
        digest.update(relative.encode("utf-8"))
        digest.update(path.read_bytes() if path.is_file() else b"<missing>")
    return digest.hexdigest()


def _reject_workspace_symlinks(workspace: Path) -> None:
    for path in workspace.rglob("*"):
        if path.is_symlink():
            raise ValueError("workspace symlinks are not allowed")


def _run_command(
    command: list[str],
    workspace: Path,
    course_assets: Path,
    hidden_root: Path | None = None,
) -> tuple[int, str, str, bool]:
    volumes: dict[str, dict[str, str]] = {
        str(workspace): {"bind": "/work", "mode": "rw"},
        str(course_assets): {"bind": "/course", "mode": "ro"},
    }
    if hidden_root:
        volumes[str(hidden_root)] = {"bind": "/hidden", "mode": "ro"}
    return run_sandbox(command=command, volumes=volumes, timeout_sec=settings.sandbox_timeout_sec)


def _compile_script(checkpoint: Checkpoint, mode: str, provided_files: list[str], hidden: bool = False) -> list[str]:
    testbench = checkpoint.hidden_testbench if hidden else (checkpoint.compile_testbench or checkpoint.public_testbench)
    testbench_path = f"/hidden/{Path(testbench).name}" if hidden else f"/course/{testbench}"
    source_paths = [f"/work/{path}" for path in checkpoint.source_files]
    if mode == "compile":
        args = ["iverilog", "-g2012", "-Wall", "-t", "null", "-s", checkpoint.hidden_top if hidden else checkpoint.top, "-o", "/tmp/elab"]
    else:
        args = ["iverilog", "-g2012", "-Wall", "-s", checkpoint.hidden_top if hidden else checkpoint.top, "-o", "/tmp/sim"]
    args.extend(source_paths)
    args.extend(f"/work/{path}" for path in provided_files)
    args.append(testbench_path)
    return args


def _simulation_command(checkpoint: Checkpoint, mode: str, provided_files: list[str], hidden: bool = False) -> list[str]:
    compile_args = _compile_script(checkpoint, mode, provided_files, hidden=hidden)
    quoted_compile = " ".join(shlex.quote(arg) for arg in compile_args)
    if mode == "compile":
        return ["bash", "-lc", quoted_compile]
    clear_waveform = "" if hidden else "rm -f /work/wave.vcd; "
    return ["bash", "-lc", f"{clear_waveform}{quoted_compile} && vvp /tmp/sim"]


def _run_phase(checkpoint: Checkpoint, workspace: Path, course_assets: Path, hidden_root: Path | None, mode: str, provided_files: list[str], hidden: bool = False) -> tuple[int, str, str, bool, Path]:
    command = _simulation_command(checkpoint, mode, provided_files, hidden=hidden)
    return (*_run_command(command, workspace, course_assets, hidden_root), workspace)


def run_checkpoint(
    course_root: Path,
    workspace_path: Path,
    checkpoint_id: str,
    mode: str,
    artifact_dir: Path | None = None,
) -> LabRunResult:
    manifest_path = course_root / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError("course manifest not found")
    import json
    from app.verilog.schemas import CourseManifest
    manifest = CourseManifest.model_validate(json.loads(manifest_path.read_text(encoding="utf-8")))
    validate_manifest(manifest, course_root)
    if manifest.toolchain == "python":
        from app.ldpc.runner import run_python_checkpoint
        return run_python_checkpoint(course_root, workspace_path, checkpoint_id, mode, artifact_dir)
    checkpoint = get_checkpoint(manifest, checkpoint_id)
    if mode not in {"compile", "test", "submit"}:
        raise ValueError(f"unsupported run mode: {mode}")

    start = time.time()
    shared_temp_root = Path(settings.data_dir) / "sandbox-runs"
    shared_temp_root.mkdir(parents=True, exist_ok=True)
    # The Docker daemon resolves bind mounts on the host, not inside the API container.
    with tempfile.TemporaryDirectory(prefix="lab-run-", dir=shared_temp_root) as temp:
        _reject_workspace_symlinks(workspace_path)
        run_workspace = Path(temp) / "work"
        shutil.copytree(workspace_path, run_workspace)
        os.chmod(run_workspace, 0o777)
        course_assets = Path(temp) / "course"
        for testbench in {checkpoint.public_testbench, checkpoint.compile_testbench or checkpoint.public_testbench}:
            source_testbench = course_root / testbench
            destination_testbench = course_assets / testbench
            destination_testbench.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_testbench, destination_testbench)
        hidden_assets = Path(temp) / "hidden"
        hidden_testbench = course_root / checkpoint.hidden_testbench
        hidden_assets.mkdir()
        shutil.copy2(hidden_testbench, hidden_assets / Path(checkpoint.hidden_testbench).name)
        for provided in manifest.provided_files:
            authored = course_root / provided
            destination = run_workspace / provided
            if authored.is_file():
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(authored, destination)
        for root, dirs, files in os.walk(run_workspace):
            for directory in dirs:
                os.chmod(Path(root) / directory, 0o777)
            for filename in files:
                os.chmod(Path(root) / filename, 0o666)

        provided_files = [path for path in manifest.provided_files if (run_workspace / path).is_file()]
        code, stdout, stderr, timed_out, _ = _run_phase(checkpoint, run_workspace, course_assets, None, "compile", provided_files)
        compile_output = (stdout + "\n" + stderr).strip()[:MAX_OUTPUT]
        compile_diagnostics = parse_diagnostics(compile_output)
        compile_ok = code == 0 and not timed_out
        if not compile_ok:
            category = "infrastructure" if code == 127 or "sandbox" in compile_output.lower() else None
            if category:
                compile_diagnostics.append(Diagnostic(category="infrastructure", message=compile_output or "sandbox failed"))
            return LabRunResult(
                stage="infrastructure" if category else "elaboration",
                compile=CompileSummary(ok=False, diagnostics=compile_diagnostics),
                timed_out=timed_out,
                runtime_ms=int((time.time() - start) * 1000),
                passed=False,
                diagnostics=compile_diagnostics,
                output=compile_output,
            )

        if mode == "compile":
            return LabRunResult(
                stage="elaboration",
                compile=CompileSummary(ok=True, diagnostics=[d for d in compile_diagnostics if d.severity == "warning"]),
                runtime_ms=int((time.time() - start) * 1000),
                passed=True,
                diagnostics=compile_diagnostics,
                output=compile_output,
            )

        public_code, public_stdout, public_stderr, public_timeout, _ = _run_phase(checkpoint, run_workspace, course_assets, None, "test", provided_files)
        public_output = (public_stdout + "\n" + public_stderr).strip()[:MAX_OUTPUT]
        public_tests, traces = parse_test_output(public_output)
        hidden_tests: TestSummary | None = None
        hidden_output = ""
        if mode == "submit" and not public_timeout and public_code == 0:
            hidden_code, hidden_stdout, hidden_stderr, hidden_timeout, _ = _run_phase(checkpoint, run_workspace, course_assets, hidden_assets, "test", provided_files, hidden=True)
            hidden_output = (hidden_stdout + "\n" + hidden_stderr).strip()[:MAX_OUTPUT]
            parsed_hidden, hidden_traces = parse_test_output(hidden_output)
            hidden_tests = TestSummary(passed=parsed_hidden.passed, failed=parsed_hidden.failed, errors=parsed_hidden.errors)
            traces.extend(hidden_traces[:32])
            if hidden_timeout:
                hidden_tests = TestSummary(passed=hidden_tests.passed, failed=hidden_tests.failed, errors=hidden_tests.errors + 1)
            hidden_ok = hidden_code == 0 and not hidden_timeout and hidden_tests.failed == 0 and hidden_tests.errors == 0
        else:
            hidden_ok = mode != "submit"

        public_ok = public_code == 0 and not public_timeout and public_tests.failed == 0 and public_tests.errors == 0 and public_tests.passed > 0
        overall = public_ok and hidden_ok
        combined = (compile_output + "\n=== PUBLIC TESTS ===\n" + public_output).strip()
        if mode == "submit":
            combined += "\n=== HIDDEN TESTS ===\n" + redact_hidden_output(hidden_output)

        artifacts: list[RunArtifact] = []
        if artifact_dir and (run_workspace / "wave.vcd").is_file():
            artifact_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(run_workspace / "wave.vcd", artifact_dir / "wave.vcd")
            artifacts.append(RunArtifact(name="wave.vcd", kind="waveform"))

        diagnostics = parse_diagnostics(public_output)
        if public_timeout:
            diagnostics.append(Diagnostic(category="simulation", message="Simulation timed out before the public testbench completed; no pass/fail counts were produced."))
        elif public_code != 0 and not public_tests.cases:
            diagnostics.append(Diagnostic(category="simulation", message=f"Simulator exited with code {public_code} before any public check completed."))
        stage = "simulation"
        return LabRunResult(
            stage=stage,
            compile=CompileSummary(ok=True, diagnostics=[d for d in compile_diagnostics if d.severity == "warning"]),
            tests=public_tests,
            hidden=hidden_tests,
            timed_out=public_timeout,
            runtime_ms=int((time.time() - start) * 1000),
            passed=overall,
            diagnostics=diagnostics,
            traces=traces[:128],
            artifacts=artifacts,
            output=combined[:MAX_OUTPUT],
        )
