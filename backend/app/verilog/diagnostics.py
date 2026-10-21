import re

from app.verilog.schemas import Diagnostic, TestCaseResult, TestSummary, TraceEvent


_DIAGNOSTIC = re.compile(r"(?P<file>[^\s:][^:]*):(?P<line>\d+)(?::(?P<column>\d+))?:?\s*(?P<message>.*)")
_TUTOR_TEST = re.compile(r"^TUTOR_TEST\s+(?P<name>\S+)\s+(?P<status>PASS|FAIL|ERROR)(?:\s+(?P<message>.*))?$")
_TUTOR_SUMMARY = re.compile(r"TUTOR_SUMMARY\s+passed=(\d+)\s+failed=(\d+)(?:\s+errors=(\d+))?")
_TUTOR_TRACE = re.compile(r"^TUTOR_TRACE\s+(?P<values>.*)$")
_PAIR = re.compile(r"(?P<key>[A-Za-z_][A-Za-z0-9_]*)=(?P<value>[^\s]+)")


def classify_message(message: str) -> str:
    lowered = message.lower()
    if any(token in lowered for token in ("syntax", "parse error", "malformed")):
        return "syntax"
    if any(token in lowered for token in ("unknown module", "port", "elaborat", "cannot find")):
        return "elaboration"
    return "unknown"


def parse_diagnostics(output: str) -> list[Diagnostic]:
    diagnostics: list[Diagnostic] = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("TUTOR_"):
            continue
        if "$finish called" in line:
            continue
        match = _DIAGNOSTIC.match(line)
        if not match:
            continue
        message = match.group("message").strip()
        lowered = message.lower()
        severity = "warning" if "warning" in lowered else "error"
        diagnostics.append(
            Diagnostic(
                severity=severity,
                category=classify_message(message),
                message=message,
                file=match.group("file"),
                line=int(match.group("line")),
                column=int(match.group("column")) if match.group("column") else None,
            )
        )
    return diagnostics


def parse_test_output(output: str) -> tuple[TestSummary, list[TraceEvent]]:
    cases: list[TestCaseResult] = []
    traces: list[TraceEvent] = []
    summary_match = _TUTOR_SUMMARY.search(output)
    for raw_line in output.splitlines():
        test_match = _TUTOR_TEST.match(raw_line.strip())
        if test_match:
            status = test_match.group("status").lower()
            cases.append(TestCaseResult(name=test_match.group("name"), status=status, message=test_match.group("message") or ""))
            continue
        trace_match = _TUTOR_TRACE.match(raw_line.strip())
        if trace_match:
            traces.append(TraceEvent(values={m.group("key"): m.group("value") for m in _PAIR.finditer(trace_match.group("values"))}))

    if summary_match:
        passed = int(summary_match.group(1))
        failed = int(summary_match.group(2))
        errors = int(summary_match.group(3) or 0)
    else:
        passed = sum(case.status == "pass" for case in cases)
        failed = sum(case.status == "fail" for case in cases)
        errors = sum(case.status == "error" for case in cases)
    return TestSummary(passed=passed, failed=failed, errors=errors, cases=cases), traces


def redact_hidden_output(output: str) -> str:
    lines = []
    for line in output.splitlines():
        if line.startswith("TUTOR_SUMMARY"):
            lines.append(line)
    return "\n".join(lines)
