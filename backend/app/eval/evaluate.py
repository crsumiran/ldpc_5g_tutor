import os
import re
import shutil
import tempfile
import time
from pathlib import Path

from app.adapters import get_adapter
from app.config import settings
from app.eval.sandbox import run_sandbox
from app.schemas import AssignmentArtifact, Evaluation, LintResult, TestCounts


def parse_pytest_output(output: str) -> tuple[int, int, int]:
    passed = 0
    failed = 0
    errors = 0

    m_pass = re.search(r"(\d+)\s+passed", output)
    if m_pass:
        passed = int(m_pass.group(1))

    m_fail = re.search(r"(\d+)\s+failed", output)
    if m_fail:
        failed = int(m_fail.group(1))

    m_err = re.search(r"(\d+)\s+error", output)
    if m_err:
        errors = int(m_err.group(1))

    return passed, failed, errors


def evaluate_submission(
    project_id: str,
    workspace_path: Path,
    assignment: AssignmentArtifact,
    hidden_dir: Path | None = None,
) -> Evaluation:
    start_time = time.time()
    adapter = get_adapter(assignment.adapter)
    if not adapter:
        return Evaluation(
            setup_ok=False,
            syntax_ok=False,
            passed=False,
            public=TestCounts(output=f"No adapter available for '{assignment.adapter}'"),
        )

    cmd = adapter.evaluate_in_container_args(assignment)

    # Use a temp directory for running so container can write output/artifacts freely without mutating learner's original files
    with tempfile.TemporaryDirectory(prefix="tutor-eval-") as tmp:
        tmp_work = Path(tmp) / "work"
        shutil.copytree(workspace_path, tmp_work)
        # Give uid 1000 full access
        os.chmod(tmp_work, 0o777)
        for root, dirs, files in os.walk(tmp_work):
            for d in dirs:
                os.chmod(os.path.join(root, d), 0o777)
            for f in files:
                os.chmod(os.path.join(root, f), 0o666)

        volumes: dict[str, dict[str, str]] = {
            str(tmp_work): {"bind": "/work", "mode": "rw"}
        }

        if hidden_dir and hidden_dir.exists() and any(hidden_dir.iterdir()):
            volumes[str(hidden_dir)] = {"bind": "/hidden", "mode": "ro"}

        exit_code, stdout, stderr, timed_out = run_sandbox(
            command=cmd,
            volumes=volumes,
            timeout_sec=settings.sandbox_timeout_sec,
        )

    runtime_ms = int((time.time() - start_time) * 1000)
    full_output = (stdout + "\n" + stderr).strip()

    # Syntax check
    syntax_ok = "SyntaxError" not in full_output and "IndentationError" not in full_output

    if assignment.adapter == "python_pytest":
        passed_cnt, failed_cnt, err_cnt = parse_pytest_output(full_output)
        overall_passed = (exit_code == 0) and (failed_cnt == 0) and (err_cnt == 0) and (passed_cnt > 0) and not timed_out
        public_counts = TestCounts(
            passed=passed_cnt,
            failed=failed_cnt,
            errors=err_cnt,
            output=full_output,
        )
    elif assignment.adapter == "sql_duckdb":
        overall_passed = ("ALL_TESTS_PASSED" in full_output) and (exit_code == 0) and not timed_out
        public_counts = TestCounts(
            passed=1 if overall_passed else 0,
            failed=0 if overall_passed else 1,
            output=full_output,
        )
    else:
        overall_passed = False
        public_counts = TestCounts(output="Plan-only adapter cannot be evaluated.")

    return Evaluation(
        setup_ok=True,
        syntax_ok=syntax_ok,
        public=public_counts,
        hidden=TestCounts(),
        lint=LintResult(ok=True),
        timed_out=timed_out,
        runtime_ms=runtime_ms,
        passed=overall_passed,
        rubric_scores={"correctness": 1.0 if overall_passed else 0.0},
    )
