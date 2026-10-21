from app.verilog.diagnostics import parse_diagnostics, parse_test_output, redact_hidden_output


def test_parse_iverilog_diagnostic():
    diagnostics = parse_diagnostics("rtl/cache.v:14: syntax error\nrtl/cache.v:15: warning: signal is unused")
    assert diagnostics[0].category == "syntax"
    assert diagnostics[0].line == 14
    assert diagnostics[1].severity == "warning"


def test_parse_structured_tests_and_trace():
    summary, traces = parse_test_output(
        "TUTOR_TEST warm_hit PASS\n"
        "TUTOR_TEST conflict FAIL expected=1 actual=0\n"
        "TUTOR_TRACE cycle=8 addr=10 state=MISS\n"
        "TUTOR_SUMMARY passed=1 failed=1"
    )
    assert summary.passed == 1
    assert summary.failed == 1
    assert summary.cases[1].message == "expected=1 actual=0"
    assert traces[0].values["state"] == "MISS"


def test_hidden_output_only_keeps_summary():
    assert redact_hidden_output("secret input\nTUTOR_SUMMARY passed=3 failed=0\n") == "TUTOR_SUMMARY passed=3 failed=0"
