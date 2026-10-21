import tempfile
from pathlib import Path

import docker
from docker.errors import ContainerError, ImageNotFound

from app.config import settings
from app.models import ExecResult

_SHELL = """
set -e
cp /in/student.v /work/and2.v
cp /lesson/tb_and2.v /work/tb_and2.v
cd /work
iverilog -o sim and2.v tb_and2.v
vvp sim
"""


def run_verilog(lesson_id: str, student_src: str) -> ExecResult:
    lesson = Path(settings.curriculum_dir) / lesson_id
    tb = lesson / f"tb_{lesson_id}.v"
    if not tb.is_file():
        return ExecResult(
            compile_ok=False,
            passed=False,
            stdout="",
            stderr=f"unknown lesson: {lesson_id}",
            exit_code=2,
        )

    if len(student_src.encode("utf-8")) > 20000:
        return ExecResult(
            compile_ok=False,
            passed=False,
            stdout="",
            stderr="rejected: source exceeds 20000 bytes",
            exit_code=2,
        )

    _FORBIDDEN = ("`include", "$readmem", "$fopen", "fork", "c_os")
    if any(token in student_src for token in _FORBIDDEN):
        return ExecResult(
            compile_ok=False,
            passed=False,
            stdout="",
            stderr="rejected: forbidden construct detected",
            exit_code=2,
        )

    client = docker.from_env()
    with tempfile.TemporaryDirectory(prefix="vt-") as tmp:
        student_path = Path(tmp) / "student.v"
        student_path.write_text(student_src, encoding="utf-8")
        try:
            out = client.containers.run(
                settings.sandbox_image,
                command=["bash", "-lc", _SHELL],
                network_disabled=True,
                mem_limit=settings.sandbox_mem,
                nano_cpus=500_000_000,
                read_only=True,
                cap_drop=["ALL"],
                security_opt=["no-new-privileges:true"],
                tmpfs={"/work": "rw,size=16m,uid=1000", "/tmp": "rw,size=8m,uid=1000"},
                volumes={
                    str(student_path.parent): {"bind": "/in", "mode": "ro"},
                    str(lesson): {"bind": "/lesson", "mode": "ro"},
                },
                working_dir="/work",
                remove=True,
                stdout=True,
                stderr=True,
            )
            text = out.decode("utf-8", errors="replace") if isinstance(out, bytes) else str(out)
            passed = "ALL_TESTS_PASSED" in text
            return ExecResult(
                compile_ok=True,
                passed=passed,
                stdout=text,
                stderr="",
                exit_code=0,
            )
        except ImageNotFound:
            return ExecResult(
                compile_ok=False,
                passed=False,
                stdout="",
                stderr="sandbox image missing; run TASK 01",
                exit_code=127,
            )
        except ContainerError as exc:
            err = (exc.stderr or b"").decode("utf-8", errors="replace")
            compile_ok = "iverilog" not in err.lower() or "error" not in err.lower()
            if "syntax" in err.lower() or "error:" in err.lower():
                compile_ok = False
            return ExecResult(
                compile_ok=compile_ok,
                passed=False,
                stdout="",
                stderr=err or str(exc),
                exit_code=exc.exit_status or 1,
            )