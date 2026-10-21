import json
from pathlib import Path
from unittest.mock import patch

import httpx

from app.verilog.manifest import load_course
from app.verilog.schemas import CompileSummary, LabRunResult, TestCaseResult as CaseResult, TestSummary as Summary
from app.verilog.tutor import get_tutor_reply
from app.verilog.waveform import response_pulses


def test_tutor_fallback_is_actionable_without_model():
    manifest, _ = load_course("cache-lab")
    checkpoint = manifest.checkpoints[0]
    with patch("app.verilog.tutor.settings.openrouter_api_key", ""):
        reply, content = get_tutor_reply(checkpoint, {"rtl/cache_address_decode.v": "module cache_address_decode; endmodule"}, "I am stuck")
    assert reply.error_category == "none"
    assert "next" in content.lower()


def test_write_handshake_question_gets_direct_answer_without_run():
    manifest, _ = load_course("cache-lab")
    checkpoint = manifest.checkpoints[4]
    question = "If there is a write operation should I wait till write is accepted by memory channel before moving to IDLE state?"
    with patch("app.verilog.tutor.settings.openrouter_api_key", ""):
        reply, content = get_tutor_reply(checkpoint, {}, question)
    assert reply.summary.startswith("Do not return to IDLE merely")
    assert "mem_req_ready" in content
    assert "mem_resp_valid" in content
    assert "No run evidence yet" not in content
    assert "run the compiler" not in content


def test_model_receives_question_and_contract_without_requiring_a_run():
    manifest, _ = load_course("cache-lab")
    checkpoint = manifest.checkpoints[4]
    question = "Should a write return to IDLE when memory accepts the request?"
    model_reply = {
        "summary": "No. mem_req_ready accepts the request, but wait for mem_resp_valid before the CPU response and IDLE.",
        "error_category": "none",
        "evidence": ["The CACHE-05 contract requires waiting for mem_resp_valid after every memory write."],
        "concept": "valid/ready handshakes",
        "next_step": "Mark the acceptance and response edges on your state diagram.",
        "question": "What holds the saved write data stable before acceptance?",
        "hint_level": 0,
    }
    with patch("app.verilog.tutor.settings.openrouter_api_key", "test"), patch(
        "app.verilog.tutor.complete", return_value={"content": f"```json\n{json.dumps(model_reply)}\n```"}
    ) as mocked:
        reply, _ = get_tutor_reply(checkpoint, {}, question)
    assert reply.summary == model_reply["summary"]
    prompt = mocked.call_args.kwargs["messages"][1]["content"]
    assert question in prompt
    assert "wait for mem_resp_valid" in prompt
    assert '"run": null' in prompt
    assert "do not tell the learner to compile first" in prompt
    assert mocked.call_args.kwargs["include_model"] is True
    assert mocked.call_args.kwargs["response_format"]["type"] == "json_schema"
    assert mocked.call_args.kwargs["plugins"] == [{"id": "response-healing"}]
    assert "google/gemma-4-26b-a4b-it:free" in mocked.call_args.kwargs["fallback_models"]
    assert "cohere/north-mini-code:free" in mocked.call_args.kwargs["fallback_models"]


def test_user_key_and_selected_model_override_server_defaults():
    manifest, _ = load_course("cache-lab")
    model_reply = {
        "summary": "The address is split into tag, index, and byte offset.",
        "error_category": "none", "evidence": ["The checkpoint requires address fields."],
        "concept": "address decoding", "next_step": "Mark the field widths.",
        "question": "Which bits select the cache line?", "hint_level": 0,
    }
    with patch("app.verilog.tutor.settings.openrouter_api_key", ""), patch(
        "app.verilog.tutor.complete", return_value={"content": json.dumps(model_reply), "_served_model": "nvidia/nemotron-3-ultra-550b-a55b:free"}
    ) as mocked:
        reply, content = get_tutor_reply(
            manifest.checkpoints[0], {}, "How is the address split?",
            model_override="nvidia/nemotron-3-ultra-550b-a55b:free", api_key_override="sk-or-v1-test-only",
            allow_model_fallbacks=False,
        )
    assert reply.source == "model"
    assert reply.model == "nvidia/nemotron-3-ultra-550b-a55b:free"
    assert "sk-or-v1-test-only" not in content
    assert mocked.call_args.kwargs["api_key"] == "sk-or-v1-test-only"
    assert mocked.call_args.kwargs["model"] == "nvidia/nemotron-3-ultra-550b-a55b:free"
    assert mocked.call_args.kwargs["fallback_models"] == []


def test_selected_model_uses_configured_model_fallbacks_by_default():
    manifest, _ = load_course("cache-lab")
    model_reply = {
        "summary": "Use the checkpoint contract.", "error_category": "none", "evidence": [],
        "concept": "address decoding", "next_step": "Mark the fields.",
        "question": "Which bits form the index?", "hint_level": 0,
    }
    with patch("app.verilog.tutor.settings.openrouter_api_key", "test"), patch(
        "app.verilog.tutor.complete", return_value={"content": json.dumps(model_reply), "_served_model": "cohere/north-mini-code:free"}
    ) as mocked:
        reply, _ = get_tutor_reply(
            manifest.checkpoints[0], {}, "Help with the fields",
            model_override="google/gemma-4-31b-it:free",
        )
    assert reply.model == "cohere/north-mini-code:free"
    assert "cohere/north-mini-code:free" in mocked.call_args.kwargs["fallback_models"]
    assert "google/gemma-4-31b-it:free" not in mocked.call_args.kwargs["fallback_models"]


def test_malformed_model_answer_retries_with_another_configured_model():
    manifest, _ = load_course("cache-lab")
    valid = {
        "summary": "The retry produced valid guidance.", "error_category": "none", "evidence": [],
        "concept": "address decoding", "next_step": "Mark the fields.",
        "question": "Which bits form the index?", "hint_level": 0,
    }
    with patch("app.verilog.tutor.settings.openrouter_api_key", "test"), patch(
        "app.verilog.tutor.complete",
        side_effect=[
            {"content": "not JSON", "_served_model": "google/gemma-4-31b-it:free"},
            {"content": json.dumps(valid), "_served_model": "cohere/north-mini-code:free"},
        ],
    ) as mocked:
        reply, content = get_tutor_reply(manifest.checkpoints[0], {}, "Help with the fields")
    assert mocked.call_count == 2
    assert mocked.call_args_list[1].kwargs["model"] == "google/gemma-4-26b-a4b-it:free"
    assert reply.source == "model"
    assert reply.model == "cohere/north-mini-code:free"
    assert "Guide model: cohere/north-mini-code:free" in content


def test_malformed_exact_model_answer_reports_actionable_status():
    manifest, _ = load_course("cache-lab")
    with patch("app.verilog.tutor.settings.openrouter_api_key", "test"), patch(
        "app.verilog.tutor.complete",
        return_value={"content": "not JSON", "_served_model": "example/model:free"},
    ):
        reply, content = get_tutor_reply(
            manifest.checkpoints[0], {}, "Help with the fields",
            model_override="example/model:free", allow_model_fallbacks=False,
        )
    assert reply.source == "fallback"
    assert "malformed structured response from example/model:free" in (reply.provider_status or "")
    assert "JSONDecodeError" not in content


def test_plain_text_model_answer_uses_deterministic_fields_instead_of_failing_json_decode():
    manifest, _ = load_course("cache-lab")
    plain_answer = "Request acceptance and operation completion are separate handshake events."
    with patch("app.verilog.tutor.settings.openrouter_api_key", "test"), patch(
        "app.verilog.tutor.complete",
        return_value={"content": plain_answer, "_served_model": "example/model:free"},
    ):
        reply, content = get_tutor_reply(
            manifest.checkpoints[0], {}, "What is the difference?",
            model_override="example/model:free", allow_model_fallbacks=False,
        )
    assert reply.source == "model"
    assert reply.summary == plain_answer
    assert reply.next_step
    assert "Guide model: example/model:free" in content
    assert "JSONDecodeError" not in content


def test_model_json_type_mismatches_use_safe_deterministic_defaults():
    manifest, _ = load_course("cache-lab")
    loose = {
        "summary": "Mark the tag, index, and offset fields.",
        "error_category": "made-up-category",
        "evidence": "The checkpoint requires address fields.",
        "hint_level": "Intermediate",
    }
    with patch("app.verilog.tutor.settings.openrouter_api_key", "test"), patch(
        "app.verilog.tutor.complete",
        return_value={"content": json.dumps(loose), "_served_model": "example/model:free"},
    ):
        reply, _ = get_tutor_reply(
            manifest.checkpoints[0], {}, "How is the address split?",
            requested_hint_level=1, model_override="example/model:free", allow_model_fallbacks=False,
        )
    assert reply.source == "model"
    assert reply.error_category == "none"
    assert reply.evidence == ["The checkpoint requires address fields."]
    assert reply.hint_level == 1
    assert reply.concept


def test_generic_model_answer_to_write_question_uses_grounded_fallback():
    manifest, _ = load_course("cache-lab")
    checkpoint = manifest.checkpoints[4]
    generic = {
        "summary": "Start with the checkpoint contract and run the compiler.",
        "error_category": "none",
        "evidence": [],
        "concept": "finite-state machines",
        "next_step": "Read the port list.",
        "question": "What is unclear?",
        "hint_level": 0,
    }
    with patch("app.verilog.tutor.settings.openrouter_api_key", "test"), patch(
        "app.verilog.tutor.complete", return_value={"content": json.dumps(generic)}
    ):
        reply, _ = get_tutor_reply(checkpoint, {}, "Should I wait for a write to be accepted before IDLE?")
    assert reply.summary.startswith("Do not return to IDLE merely")


def test_waveform_fallback_explains_read_miss_sampling_mismatch():
    manifest, root = load_course("cache-lab")
    checkpoint = manifest.checkpoints[4]
    run = LabRunResult(
        stage="simulation",
        compile=CompileSummary(ok=True),
        tests=Summary(
            passed=2,
            failed=2,
            cases=[CaseResult(name="read_miss", status="fail", message="expected_data=20000009 expected_hit=0 actual_data=00000000 actual_hit=0")],
        ),
    )
    pulses = [{"start": "55 ns", "end": "65 ns", "data": "0x20000009", "data_after": "0x00000000", "hit": "0"}]
    with patch("app.verilog.tutor.settings.openrouter_api_key", ""):
        reply, content = get_tutor_reply(
            checkpoint, {}, "The read miss data is right in the waveform. Why does it fail?", run,
            public_testbench=(root / checkpoint.public_testbench).read_text(), waveform_pulses=pulses,
            checker_changed_since_run=True,
        )
    assert "55 ns" in content
    assert "65 ns" in content
    assert "cycle late" in reply.summary
    assert "0x20000009" in reply.summary


def test_waveform_parser_captures_response_window(tmp_path: Path):
    waveform = tmp_path / "wave.vcd"
    waveform.write_text(
        "$timescale 1ps $end\n$scope module tb_controller $end\n"
        "$var wire 1 ! cpu_resp_valid $end\n$var wire 32 @ cpu_resp_rdata [31:0] $end\n"
        "$var wire 1 # cpu_resp_hit $end\n$upscope $end\n$enddefinitions $end\n"
        "#0\n0!\nb0 @\n0#\n#55000\n1!\nb100000000000000000000000001001 @\n0#\n"
        "#65000\n0!\nb0 @\n"
    )
    assert response_pulses(waveform) == [
        {"start": "55 ns", "data": "0x20000009", "hit": "0", "memory_data": "unknown", "end": "65 ns", "data_after": "0x00000000"}
    ]


def test_provider_http_failure_is_visible_not_silent():
    manifest, _ = load_course("cache-lab")
    request = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")
    response = httpx.Response(429, request=request)
    error = httpx.HTTPStatusError("rate limited", request=request, response=response)
    with patch("app.verilog.tutor.settings.openrouter_api_key", "test"), patch("app.verilog.tutor.complete", side_effect=error) as mocked:
        reply, content = get_tutor_reply(manifest.checkpoints[4], {}, "Why did my test fail?")
    assert reply.source == "fallback"
    assert reply.provider_status is not None and "OpenRouter HTTP 429" in reply.provider_status
    assert "Guide model unavailable (OpenRouter HTTP 429" in content
    assert mocked.call_count == 1


def test_model_read_timeout_tries_one_configured_fallback():
    manifest, _ = load_course("cache-lab")
    fallback_model = "cohere/north-mini-code:free"
    model_reply = {
        "summary": "mem_req_ready accepts the request; mem_resp_valid marks its completion before the CPU response.",
        "error_category": "none",
        "evidence": ["The checkpoint requires waiting for mem_resp_valid after mem_req_ready."],
        "concept": "memory response handshake",
        "next_step": "Trace the request and response handshakes separately.",
        "question": "Which signal marks the memory response?",
        "hint_level": 0,
    }
    request = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")
    with patch("app.verilog.tutor.settings.openrouter_api_key", "test"), patch(
        "app.verilog.tutor.settings.tutor_fallback_models", fallback_model
    ), patch(
        "app.verilog.tutor.complete",
        side_effect=[
            httpx.ReadTimeout("upstream did not respond", request=request),
            {"content": json.dumps(model_reply), "_served_model": fallback_model},
        ],
    ) as mocked:
        reply, _ = get_tutor_reply(
            manifest.checkpoints[4], {}, "Explain the write response handshake.",
            model_override="nvidia/nemotron-3-ultra-550b-a55b:free",
        )

    assert reply.source == "model"
    assert reply.model == fallback_model
    assert mocked.call_count == 2
    assert mocked.call_args_list[0].kwargs["model"] == "nvidia/nemotron-3-ultra-550b-a55b:free"
    assert mocked.call_args_list[1].kwargs["model"] == fallback_model
    assert mocked.call_args_list[1].kwargs["fallback_models"] == []


def test_write_through_fallback_uses_current_source_only():
    manifest, _ = load_course("cache-lab")
    run = LabRunResult(
        stage="simulation",
        compile=CompileSummary(ok=True),
        tests=Summary(
            passed=3,
            failed=1,
            cases=[CaseResult(name="write_through", status="fail")],
        ),
    )
    files = {"rtl/cache_controller.v": "always @(*) begin\n  int_mem_req_wdata = 32'h00000000;\nend\n"}
    with patch("app.verilog.tutor.settings.openrouter_api_key", ""):
        reply, _ = get_tutor_reply(manifest.checkpoints[4], files, "Why does write-through fail?", run)
        stale, _ = get_tutor_reply(manifest.checkpoints[4], files, "Why does write-through fail?", run, source_matches_run=False)
    assert "only assigned zero" in reply.summary
    assert "rtl/cache_controller.v:2" in reply.evidence[1]
    assert "only assigned zero" not in stale.summary


def test_zero_case_timeout_explains_reset_polarity_even_for_old_misclassified_run():
    manifest, root = load_course("cache-lab")
    checkpoint = manifest.checkpoints[4]
    testbench = (root / checkpoint.public_testbench).read_text()
    files = {"rtl/cache_controller.v": "always @(posedge clk or negedge reset) begin\n  if (!reset) state <= IDLE;\nend\n"}
    run = LabRunResult(stage="simulation", compile=CompileSummary(ok=True), tests=Summary(), runtime_ms=32345, timed_out=False)
    with patch("app.verilog.tutor.settings.openrouter_api_key", ""):
        reply, content = get_tutor_reply(checkpoint, files, "Why are there 0 passed and 0 failed?", run, public_testbench=testbench)
    assert reply.error_category == "timeout"
    assert "0 passed / 0 failed" in reply.summary
    assert "reset to 0" in reply.summary
    assert "if (!reset)" in content
    assert "rerun" in reply.next_step


def test_model_answer_contradicting_reset_evidence_is_rejected():
    manifest, root = load_course("cache-lab")
    checkpoint = manifest.checkpoints[4]
    run = LabRunResult(stage="simulation", compile=CompileSummary(ok=True), tests=Summary(), runtime_ms=32345)
    files = {"rtl/cache_controller.v": "always @(posedge clk or negedge reset) begin\n  if (!reset) state <= IDLE;\nend\n"}
    bad = {
        "summary": "This run does not identify an RTL defect. Rerun unchanged.",
        "error_category": "none", "evidence": ["No tests reported."],
        "concept": "FSM", "next_step": "Rerun unchanged.", "question": "What happened?", "hint_level": 0,
    }
    with patch("app.verilog.tutor.settings.openrouter_api_key", "test"), patch(
        "app.verilog.tutor.complete", return_value={"content": json.dumps(bad), "_served_model": "nex-agi/nex-n2.5-pro:free"}
    ) as mocked:
        reply, content = get_tutor_reply(checkpoint, files, "Why did 0/0 happen?", run, public_testbench=(root / checkpoint.public_testbench).read_text())
    assert reply.source == "fallback"
    assert "reset" in reply.summary.lower()
    assert "ignored reset-polarity evidence" in content
    assert "verified_diagnostic" in mocked.call_args.kwargs["messages"][1]["content"]


def test_stale_source_is_not_blamed_for_old_timeout():
    manifest, root = load_course("cache-lab")
    checkpoint = manifest.checkpoints[4]
    run = LabRunResult(stage="simulation", compile=CompileSummary(ok=True), tests=Summary(), runtime_ms=32345)
    files = {"rtl/cache_controller.v": "always @(posedge clk or negedge reset) begin\n  if (!reset) state <= IDLE;\nend\n"}
    with patch("app.verilog.tutor.settings.openrouter_api_key", ""):
        reply, _ = get_tutor_reply(checkpoint, files, "Why did 0/0 happen?", run, public_testbench=(root / checkpoint.public_testbench).read_text(), source_matches_run=False)
    assert "your controller" not in reply.summary
    assert "no public checks" in reply.summary


def test_tutor_rejects_reference_leak_from_model():
    manifest, root = load_course("cache-lab")
    checkpoint = manifest.checkpoints[0]
    leaking = {
        "summary": "Try this",
        "error_category": "none",
        "evidence": [],
        "concept": "bit slicing",
        "next_step": "assign tag = addr[7:4]; assign index = addr[3:2]; assign byte_offset = addr[1:0];",
        "question": "What are the field widths?",
        "hint_level": 1,
    }
    with patch("app.verilog.tutor.settings.openrouter_api_key", "test"), patch("app.verilog.tutor.complete", return_value={"content": json.dumps(leaking)}):
        reply, content = get_tutor_reply(
            checkpoint,
            {"rtl/cache_address_decode.v": (root / "starter/rtl/cache_address_decode.v").read_text()},
            "help",
            reference_files={"rtl/cache_address_decode.v": (root / "reference/rtl/cache_address_decode.v").read_text()},
        )
    assert "assign tag = addr[7:4]" not in content
    assert reply.next_step != leaking["next_step"]
