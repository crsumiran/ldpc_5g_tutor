from app.eval.sandbox import _is_timeout_exit, run_sandbox


def test_timeout_exit_detects_sigkill_at_deadline_only():
    assert _is_timeout_exit(124, 30, 30)
    assert _is_timeout_exit(137, 30.1, 30)
    assert not _is_timeout_exit(137, 1, 30)
    assert not _is_timeout_exit(0, 31, 30)


def test_sandbox_network_disabled():
    # Attempting to open a socket connection to a public IP should fail
    network_probe_cmd = [
        "python3",
        "-c",
        "import socket; s = socket.socket(); s.settimeout(2); s.connect(('1.1.1.1', 53))",
    ]

    exit_code, stdout, stderr, timed_out = run_sandbox(
        command=network_probe_cmd,
        volumes={},
        timeout_sec=5,
    )

    assert exit_code != 0
    assert "OSError" in stderr or "Network is unreachable" in stderr or "TimeoutError" in stderr or timed_out or exit_code == 1
