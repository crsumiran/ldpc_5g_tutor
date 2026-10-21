"""Public-only, fresh-process Python learning checks; not adversarial grading."""
import json
import os
import shutil
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from tempfile import TemporaryDirectory

from app.config import settings
from app.eval.sandbox import run_sandbox
from app.verilog.manifest import load_course, get_checkpoint
from app.verilog.schemas import Diagnostic, LabRunResult, RunArtifact, TestCaseResult, TestSummary


def parse_report(path: Path, expected: int) -> TestSummary:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 512 * 1024:
        return TestSummary(errors=1, cases=[TestCaseResult(name="report", status="error", message="No complete public report. Zero checks is not a pass.")])
    try:
        cases = []
        for item in ET.parse(path).getroot().iter("testcase"):
            failure = item.find("failure")
            error = item.find("error")
            skipped = item.find("skipped")
            problem = failure if failure is not None else error if error is not None else skipped
            status = "fail" if failure is not None else "error" if problem is not None else "pass"
            cases.append(TestCaseResult(name=item.get("name", "check"), status=status, message=((problem.text or problem.get("message", ""))[:2500] if problem is not None else "")))
        if len(cases) != expected:
            cases.append(TestCaseResult(name="collection_count", status="error", message=f"Expected {expected} public checks, collected {len(cases)}. Incomplete collection is not a pass."))
        return TestSummary(passed=sum(c.status == "pass" for c in cases), failed=sum(c.status == "fail" for c in cases), errors=sum(c.status == "error" for c in cases), cases=cases)
    except (ET.ParseError, ValueError):
        return TestSummary(errors=1, cases=[TestCaseResult(name="report", status="error", message="Malformed public report.")])


def run_python_checkpoint(root, workspace, checkpoint_id, mode, artifact_dir=None):
    course_id = json.loads((root / "manifest.json").read_text(encoding="utf-8"))["id"]
    manifest, _ = load_course(course_id, root.parent)
    checkpoint = get_checkpoint(manifest, checkpoint_id)
    if mode not in {"compile", "test", "submit"}:
        raise ValueError("Unsupported Python run mode")
    began = time.monotonic()
    shared = Path(settings.data_dir) / "sandbox-runs"
    shared.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="python-", dir=shared) as temp:
        work = Path(temp) / "work"
        work.mkdir()
        for relative in checkpoint.source_files:
            source = (workspace / relative).resolve()
            if not source.is_relative_to(workspace.resolve()) or (workspace / relative).is_symlink():
                raise ValueError("Unsafe source path")
            if source.stat().st_size > 256 * 1024:
                raise ValueError("Source too large")
            target = work / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        for relative in manifest.provided_files:
            target = work / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(root / relative, target)
        if artifact_dir:
            artifact_dir.mkdir(parents=True, exist_ok=True)
            snapshot = artifact_dir / "source"
            shutil.copytree(work, snapshot, dirs_exist_ok=True)
        for directory, _, files in os.walk(work):
            os.chmod(directory, 0o777)
            for name in files:
                os.chmod(Path(directory) / name, 0o666)
        volumes = {str(work): {"bind": "/work", "mode": "rw"}}
        # AST parsing validates syntax without importing or executing student code.
        syntax = "import ast,pathlib; [ast.parse(p.read_text(),filename=str(p)) for p in pathlib.Path('/work').rglob('*.py')]"
        code, stdout, stderr, timeout = run_sandbox(["python3", "-c", syntax], volumes, settings.sandbox_timeout_sec)
        output = (stdout + stderr)[:128 * 1024]
        if code or timeout or mode == "compile":
            ok = code == 0 and not timeout
            diagnostic = [] if ok else [Diagnostic(category="syntax" if code != 127 else "infrastructure", message=output[-4000:] or "Syntax check timed out")]
            return LabRunResult(stage="compile", compile={"ok": ok, "diagnostics": diagnostic}, passed=ok, timed_out=timeout, diagnostics=diagnostic, runtime_ms=int((time.monotonic()-began)*1000), output=output)
        # Only the one public suite is mounted. No private/reference directory.
        public = Path(temp) / "public"
        public.mkdir()
        shutil.copy2(root / checkpoint.public_testbench, public / "test_assignment.py")
        if manifest.id == "ldpc-5g":
            # Trusted public expectations, not a reference implementation.
            teaching = json.loads((root / "public_cases.json").read_text(encoding="utf-8"))
            (public / "teaching_case.json").write_text(json.dumps(teaching[checkpoint.id]), encoding="utf-8")
            shutil.copy2(root / "tests/teaching_conftest.py", public / "conftest.py")
        volumes[str(public)] = {"bind": "/public", "mode": "ro"}
        code, stdout, stderr, timeout = run_sandbox(["python3", "-m", "pytest", "-q", "-s", "-p", "no:cacheprovider", "--override-ini=pythonpath=/work/python", "--junitxml=/work/report.xml", "/public/test_assignment.py"], volumes, settings.sandbox_timeout_sec)
        output = (stdout + stderr)[:128 * 1024]
        report = parse_report(work / "report.xml", checkpoint.expected_public_checks)
        passed = code == 0 and not timeout and report.passed == checkpoint.expected_public_checks and not report.failed and not report.errors
        artifacts = []
        if artifact_dir:
            payload = {"checkpoint": checkpoint.id, "public_only": True, "tests": report.model_dump(), "output": output}
            (artifact_dir / "public-report.json").write_text(json.dumps(payload, indent=2))
            artifacts = [RunArtifact(name="public-report.json", kind="log")]
        diagnostics = [Diagnostic(category="simulation", message="Python run exceeded its time budget; incomplete checks do not pass.")] if timeout else []
        return LabRunResult(stage="simulation", compile={"ok": True}, tests=report, passed=passed, timed_out=timeout, runtime_ms=int((time.monotonic()-began)*1000), diagnostics=diagnostics, output=output, artifacts=artifacts)
