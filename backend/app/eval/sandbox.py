import logging
import time
from typing import Any
import docker
from docker.errors import ContainerError, ImageNotFound

from app.config import settings

logger = logging.getLogger(__name__)


def _is_timeout_exit(exit_code: int, elapsed: float, timeout_sec: int) -> bool:
    # GNU timeout exits 124 on a normal expiry and 137 when the wrapper uses SIGKILL.
    # A quick SIGKILL for another reason must not be reported as a timeout.
    return exit_code == 124 or (exit_code == 137 and elapsed >= max(0, timeout_sec - 1))


def run_sandbox(
    command: list[str],
    volumes: dict[str, dict[str, str]],
    timeout_sec: int = 30,
) -> tuple[int, str, str, bool]:
    client = docker.from_env()
    container = None

    try:
        container = client.containers.create(
            image=settings.sandbox_image,
            command=command,
            network_disabled=True,
            mem_limit=settings.sandbox_mem,
            nano_cpus=1_000_000_000,
            read_only=True,
            cap_drop=["ALL"],
            security_opt=["no-new-privileges:true"],
            tmpfs={"/tmp": "rw,size=16m,uid=1000"},
            volumes=volumes,
            working_dir="/work",
            user="1000:1000",
            pids_limit=128,
            environment={"TIMEOUT": str(timeout_sec)},
        )

        container.start()
        started_at = time.monotonic()
        res = container.wait(timeout=timeout_sec + 5)
        exit_code = res.get("StatusCode", 1)
        elapsed = time.monotonic() - started_at
        timed_out = _is_timeout_exit(exit_code, elapsed, timeout_sec)
        logs = container.logs(stdout=True, stderr=True)
        container.remove(v=True, force=True)
        container = None

        text = logs.decode("utf-8", errors="replace") if isinstance(logs, bytes) else str(logs)
        return exit_code, text, "", timed_out
    except ContainerError as e:
        err = (e.stderr or b"").decode("utf-8", errors="replace")
        return e.exit_status or 1, "", err, False
    except ImageNotFound:
        return 127, "", f"Sandbox image '{settings.sandbox_image}' not found.", False
    except Exception as e:
        logger.exception(f"Sandbox error: {e}")
        return 1, "", str(e), "timeout" in str(e).lower()
    finally:
        if container is not None:
            try:
                container.remove(v=True, force=True)
            except Exception:
                logger.warning("Unable to remove sandbox container", exc_info=True)
