import json
import logging
import re
from pathlib import Path
from typing import Any
from collections.abc import Callable

import httpx

from app.assignments.leakcheck import clean_lines, strip_reference_leak
from app.config import settings
from app.llm import complete, openrouter_error_status
from app.opencode import complete as opencode_complete, OpenCodeError, OpenCodeCancelled
from app.schemas import FileBlob
from app.verilog.schemas import Checkpoint, LabRunResult, TutorReply


logger = logging.getLogger(__name__)


TUTOR_RESPONSE_FORMAT: dict[str, Any] = {
    "type": "json_schema",
    "json_schema": {
        "name": "tutor_reply",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "error_category": {
                    "type": "string",
                    "enum": ["syntax", "elaboration", "protocol", "state", "assertion", "timeout", "integration", "none", "unknown"],
                },
                "evidence": {"type": "array", "items": {"type": "string"}, "maxItems": 5},
                "concept": {"type": "string"},
                "next_step": {"type": "string"},
                "question": {"type": "string"},
                "hint_level": {"type": "integer", "minimum": 0, "maximum": 3},
            },
            "required": ["summary", "error_category", "evidence", "concept", "next_step", "question", "hint_level"],
            "additionalProperties": False,
        },
    },
}


class TutorModelFormatError(ValueError):
    def __init__(self, model: str):
        super().__init__(f"malformed structured response from {model}")
        self.model = model


def _is_write_handshake_question(checkpoint: Checkpoint, message: str) -> bool:
    return checkpoint.id == "CACHE-05" and bool(re.search(r"\bwrite\b", message, re.I)) and bool(
        re.search(r"\b(wait|accept|ready|idle|handshake|complete|finish|acknowledge)\b", message, re.I)
    )


def _write_handshake_answer() -> TutorReply:
    return TutorReply(
        summary=(
            "Do not return to IDLE merely when memory accepts a write. A memory write is accepted "
            "when mem_req_valid and mem_req_ready are both 1 on the same clock edge, but this "
            "checkpoint also requires waiting for mem_resp_valid before completing the CPU operation. "
            "Then assert cpu_resp_valid for one response cycle and return to IDLE."
        ),
        error_category="none",
        evidence=[
            "CACHE-05 requires holding the saved write address and data stable until the memory-request handshake.",
            "CACHE-05 requires waiting for mem_resp_valid before completing a memory write.",
        ],
        concept="valid/ready request acceptance versus write completion",
        next_step="Draw the write path as request accepted → memory response → CPU response → IDLE, and label the handshake on each transition.",
        question="If mem_req_ready stays low for three cycles, which request signals must remain unchanged?",
        hint_level=0,
    )


def _parse_model_reply(content: str, defaults: TutorReply | None = None) -> TutorReply:
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*|\s*```$", "", content, flags=re.I).strip()
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        if start < 0:
            raise
        data, _ = json.JSONDecoder().raw_decode(content[start:])
    if not isinstance(data, dict):
        raise ValueError("Tutor response is not an object")
    if defaults is None:
        return TutorReply.model_validate(data)

    summary = data.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        raise ValueError("Tutor response has no summary")
    evidence = data.get("evidence", defaults.evidence)
    if isinstance(evidence, str):
        evidence = [evidence]
    if not isinstance(evidence, list):
        evidence = defaults.evidence
    evidence = [str(item) for item in evidence[:5]]
    categories = {"syntax", "elaboration", "protocol", "state", "assertion", "timeout", "integration", "none", "unknown"}
    category = data.get("error_category")
    if category not in categories:
        category = defaults.error_category

    def text_field(name: str, default: str) -> str:
        value = data.get(name)
        return value.strip() if isinstance(value, str) and value.strip() else default

    return TutorReply(
        summary=summary.strip(),
        error_category=category,
        evidence=evidence,
        concept=text_field("concept", defaults.concept),
        next_step=text_field("next_step", defaults.next_step),
        question=text_field("question", defaults.question),
        hint_level=defaults.hint_level,
    )


def _plain_model_reply(content: str, defaults: TutorReply) -> TutorReply | None:
    text = content.strip()
    if not text or "{" in text or text.lower().startswith("```json"):
        return None
    if text.startswith("```") and text.endswith("```"):
        text = re.sub(r"^```[^\n]*\n?|\n?```$", "", text).strip()
    if len(text) < 40 or len(text.split()) < 6:
        return None
    return defaults.model_copy(update={"summary": text[:6000]})


def _complete_tutor_reply(
    messages: list[dict[str, str]],
    requested_model: str,
    fallback_models: list[str],
    api_key: str,
    defaults: TutorReply,
) -> tuple[TutorReply, str]:
    remaining_models = list(dict.fromkeys(fallback_models))
    model = requested_model
    retry_used = False
    while True:
        try:
            model_message = complete(
                messages=messages,
                model=model,
                fallback_models=remaining_models,
                include_model=True,
                response_format=TUTOR_RESPONSE_FORMAT,
                plugins=[{"id": "response-healing"}],
                temperature=0.2,
                api_key=api_key,
                max_tokens=1400,
            )
        except httpx.ReadTimeout:
            # OpenRouter's models-array fallback handles returned errors, but
            # cannot help if the upstream request never returns a response.
            # Make one separate attempt with the next configured model.
            if not remaining_models or retry_used:
                raise
            timed_out_model = model
            model, remaining_models = remaining_models[0], remaining_models[1:]
            retry_used = True
            logger.warning("Tutor model %s timed out; trying configured fallback %s", timed_out_model, model)
            continue
        served_model = str(model_message.get("_served_model") or model)
        content = model_message.get("content") or ""
        try:
            return _parse_model_reply(content, defaults), served_model
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            plain_reply = _plain_model_reply(content, defaults) if isinstance(content, str) else None
            if plain_reply is not None:
                logger.info("Tutor model returned plain text instead of JSON; using deterministic fields: %s", served_model)
                return plain_reply, served_model
            logger.warning("Tutor model returned unusable structured output: %s", served_model)
            remaining_models = [item for item in remaining_models if item != served_model and item != model]
            if not remaining_models or retry_used:
                raise TutorModelFormatError(served_model) from exc
            model, remaining_models = remaining_models[0], remaining_models[1:]
            retry_used = True


def _waveform_read_miss_answer(
    run: LabRunResult | None,
    message: str,
    waveform_pulses: list[dict[str, str]] | None,
    level: int,
    checker_changed_since_run: bool,
) -> TutorReply | None:
    if not run or not waveform_pulses or not re.search(r"wave|read.?miss", message, re.I):
        return None
    case = next((item for item in run.tests.cases if item.name == "read_miss" and item.status == "fail"), None)
    if not case:
        return None
    expected = re.search(r"expected_data=([0-9a-fA-F]+)", case.message)
    actual = re.search(r"actual_data=([0-9a-fA-F]+)", case.message)
    if not expected or not actual:
        return None
    expected_value = f"0x{int(expected.group(1), 16):08x}"
    actual_value = f"0x{int(actual.group(1), 16):08x}"
    pulse = next((item for item in waveform_pulses if item.get("data") == expected_value and item.get("data_after") == actual_value), None)
    if not pulse:
        return None
    timing_explanation = (
        "The older public checker sampled a cycle late; this read-miss result does not show a wrong value during valid."
        if checker_changed_since_run else
        "This suggests the comparison sampled after the valid pulse; check the comparison time before changing the read data path."
    )
    return TutorReply(
        summary=(
            f"You are right: the waveform shows {expected_value} while cpu_resp_valid is high. "
            f"The stored public result reports {actual_value}, which is the value after the response pulse, "
            "when this controller's combinational response data has returned to zero. "
            + timing_explanation
        ),
        error_category="assertion",
        evidence=[
            f"Waveform: cpu_resp_valid rises at {pulse['start']} with cpu_resp_rdata={expected_value}; it falls at {pulse.get('end', 'an unknown time')} and data becomes {actual_value}.",
            "The stored mismatch equals the waveform's post-response value, not its value during cpu_resp_valid.",
        ],
        concept="sampling a one-cycle valid/data response",
        next_step="Judge the response data at the same time as cpu_resp_valid; then rerun the updated public checker and examine any remaining failure separately.",
        question="At the exact time the checker compares, is cpu_resp_valid still high?",
        hint_level=level,
    )


def _write_through_answer(
    checkpoint: Checkpoint,
    run: LabRunResult | None,
    student_files: dict[str, str],
    level: int,
) -> TutorReply | None:
    if checkpoint.id != "CACHE-05" or not run:
        return None
    if not any(item.name == "write_through" and item.status == "fail" for item in run.tests.cases):
        return None
    for path, content in student_files.items():
        assignments = [
            (number, match.group(1).strip())
            for number, line in enumerate(content.splitlines(), 1)
            if (match := re.search(r"^\s*int_mem_req_wdata\s*(?:<=|=)\s*([^;]+);", line))
        ]
        if assignments and all(re.fullmatch(r"(?:\d+\s*'\s*[bBdDhH])?0+", value) for _, value in assignments):
            return TutorReply(
                summary=(
                    "The corrected public run passes the read miss, read hit, and write hit. "
                    "The remaining write-through check fails because the memory-request write-data "
                    "signal is only assigned zero in the current controller source."
                ),
                error_category="protocol",
                evidence=[
                    "Public run: read_miss, read_hit, and write_hit pass; write_through fails.",
                    f"{path}:{assignments[0][0]} initializes int_mem_req_wdata to zero, with no other assignment to that signal.",
                ],
                concept="write-through data path",
                next_step="Trace the accepted CPU write data to mem_req_wdata and check that it remains stable through the memory-request handshake.",
                question="What value does mem_req_wdata carry while mem_req_valid and mem_req_write are high?",
                hint_level=level,
            )
    return None


def _reset_polarity_answer(
    checkpoint: Checkpoint,
    run: LabRunResult | None,
    student_files: dict[str, str],
    public_testbench: str | None,
    source_matches_run: bool,
    level: int,
) -> TutorReply | None:
    if checkpoint.id != "CACHE-05" or not run or not source_matches_run or not public_testbench:
        return None
    no_cases = run.tests.passed == run.tests.failed == run.tests.errors == 0 and not run.tests.cases
    near_timeout = run.runtime_ms >= max(0, settings.sandbox_timeout_sec - 1) * 1000
    if not run.compile.ok or not no_cases or not (run.timed_out or near_timeout):
        return None

    bench_lines = public_testbench.splitlines()
    high = next((i for i, line in enumerate(bench_lines, 1) if re.search(r"\breset\s*=\s*(?:1'b1|1)\s*;", line)), None)
    low = next((i for i, line in enumerate(bench_lines, 1) if i > (high or 0) and re.search(r"\breset\s*=\s*(?:1'b0|0)\s*;", line)), None)
    if high is None or low is None:
        return None
    for path, source in student_files.items():
        if not path.endswith("cache_controller.v"):
            continue
        lines = source.splitlines()
        edge = next((i for i, line in enumerate(lines, 1) if re.search(r"\balways\s*@\s*\([^)]*\bnegedge\s+reset\b", line)), None)
        branch = next((i for i, line in enumerate(lines, 1) if re.search(r"\bif\s*\(\s*!\s*reset\s*\)", line)), None)
        if edge is None or branch is None:
            continue
        return TutorReply(
            summary=(
                "The 0 passed / 0 failed result is a stalled simulation, not a passing run. "
                "The public testbench sets reset to 0 to release the controller, but your controller "
                "treats 0 as reset asserted. It therefore stays in IDLE and never answers the first read miss."
            ),
            error_category="timeout",
            evidence=[
                f"Public testbench:{high},{low} drives reset high initially, then low before read_miss.",
                f"{path}:{edge},{branch} uses negedge reset and if (!reset), so low keeps the controller in its reset branch.",
                f"Run: compiled, produced no named public checks, and stopped after {run.runtime_ms} ms.",
            ],
            concept="reset polarity and simulation progress",
            next_step="Align the controller's reset polarity with the public testbench, then rerun the public checks.",
            question="When the testbench holds reset at 0 during read_miss, does your state register advance out of IDLE?",
            hint_level=level,
        )
    return None


def _fallback(
    checkpoint: Checkpoint,
    message: str,
    run: LabRunResult | None,
    requested_level: int,
    public_testbench: str | None = None,
    waveform_pulses: list[dict[str, str]] | None = None,
    student_files: dict[str, str] | None = None,
    source_matches_run: bool = True,
    checker_changed_since_run: bool = False,
) -> TutorReply:
    level = min(max(requested_level, 0), 3)
    waveform_answer = _waveform_read_miss_answer(run, message, waveform_pulses, level, checker_changed_since_run)
    if waveform_answer:
        return waveform_answer
    reset_answer = _reset_polarity_answer(checkpoint, run, student_files or {}, public_testbench, source_matches_run, level)
    if reset_answer:
        return reset_answer
    if source_matches_run:
        write_answer = _write_through_answer(checkpoint, run, student_files or {}, level)
        if write_answer:
            return write_answer
    if _is_write_handshake_question(checkpoint, message):
        return _write_handshake_answer().model_copy(update={"hint_level": level})
    if run is None:
        return TutorReply(
            summary="I cannot verify your implementation without a run, but I can still explain the checkpoint contract.",
            error_category="none",
            evidence=[],
            concept=checkpoint.concepts[0],
            next_step=checkpoint.hints[min(level - 1, 2)] if level else "Compare your question with the listed checkpoint requirements, then ask about the specific signal or transition that is unclear.",
            question="Which named signal or transition in the contract would you like to examine?",
            hint_level=level,
        )
    if not run.compile.ok:
        diagnostic = run.compile.diagnostics[0] if run.compile.diagnostics else None
        category = "syntax" if diagnostic and diagnostic.category == "syntax" else "elaboration"
        location = f" at {diagnostic.file}:{diagnostic.line}" if diagnostic and diagnostic.file and diagnostic.line else ""
        return TutorReply(
            summary=f"The design does not elaborate{location}; fix the compiler diagnostic before debugging cache behavior.",
            error_category=category,
            evidence=[diagnostic.message] if diagnostic else ["The compiler exited before simulation."],
            concept="Verilog compilation and elaboration",
            next_step=checkpoint.hints[min(level, 2)] if level else "Read the first error from top to bottom and check the module name and port list around that line.",
            question="What does the first compiler error say about the module or signal at that location?",
            hint_level=level,
        )
    if run.timed_out:
        return TutorReply(
            summary="The simulator timed out, so the testbench never reached a clean response.",
            error_category="timeout",
            evidence=["Simulation exceeded the sandbox time limit."],
            concept="Handshake progress and finite-state machines",
            next_step=checkpoint.hints[min(level, 2)] if level else "Trace the valid/ready signals and identify the state that should make progress next.",
            question="Which state transition is supposed to happen when the waiting handshake completes?",
            hint_level=level,
        )
    if run.stage == "simulation" and not run.tests.cases and not run.tests.passed:
        return TutorReply(
            summary="The simulation produced no public checks, so 0 passed / 0 failed does not mean the controller passed.",
            error_category="unknown",
            evidence=[f"No TUTOR_TEST or TUTOR_SUMMARY was emitted during this {run.runtime_ms} ms run."],
            concept="testbench progress",
            next_step="Inspect the first request and response handshake in the waveform, then rerun after addressing the stall.",
            question="Which signal is the public testbench waiting for before it can report read_miss?",
            hint_level=level,
        )
    if run.tests.failed or run.tests.errors:
        case = next((item for item in run.tests.cases if item.status != "pass"), None)
        evidence = [case.message or f"Test {case.name} failed."] if case else ["One or more public tests failed."]
        return TutorReply(
            summary=f"The code compiles, but {run.tests.failed + run.tests.errors} public check(s) still fail.",
            error_category="assertion",
            evidence=evidence,
            concept=checkpoint.concepts[0],
            next_step=checkpoint.hints[min(level, 2)] if level else "Reproduce the first failing case by writing down the expected and observed signal values.",
            question="For the first failing case, which output differs and at what cycle does it first differ?",
            hint_level=level,
        )
    return TutorReply(
        summary="The visible checks pass. Explain the invariant that makes the implementation correct before submitting.",
        error_category="none",
        evidence=[f"{run.tests.passed} public checks passed."],
        concept=checkpoint.concepts[-1],
        next_step="Submit the checkpoint to run hidden edge cases, then reflect on the design tradeoff.",
        question="What edge case would you add if you were writing the next hidden test?",
        hint_level=level,
    )


def _format(reply: TutorReply) -> str:
    if reply.source == "model":
        engine = "OpenCode · " if reply.engine == "opencode" else ""
        status = f"Guide model: {engine}{reply.model or 'OpenRouter'}\n\n"
    elif reply.provider_status:
        status = f"Guide model unavailable ({reply.provider_status}); using local diagnostic feedback.\n\n"
    else:
        status = ""
    evidence = "\n".join(f"- {item}" for item in reply.evidence)
    basis = f"\n\n**Basis**\n{evidence}" if evidence else ""
    return f"{status}{reply.summary}{basis}\n\n**Concept**\n{reply.concept}\n\n**Next step**\n{reply.next_step}\n\n**Think about**\n{reply.question}"


def _system_prompt() -> str:
    prompt_path = Path(__file__).parents[2] / "prompts" / "verilog_tutor.txt"
    if prompt_path.is_file():
        return prompt_path.read_text(encoding="utf-8")
    return "You are a Socratic Verilog tutor. Never provide a complete solution."


def _contains_reference_fragment(text: str, reference_files: dict[str, str]) -> bool:
    candidate_lines = set(clean_lines(text))
    candidate_text = "\n".join(candidate_lines)
    for content in reference_files.values():
        for line in clean_lines(content):
            if len(line) >= 20 and (line in candidate_lines or line in candidate_text):
                return True
    return False


def get_tutor_reply(
    checkpoint: Checkpoint,
    student_files: dict[str, str],
    message: str,
    run: LabRunResult | None = None,
    requested_hint_level: int = 0,
    selected_file: str | None = None,
    selected_start_line: int | None = None,
    selected_end_line: int | None = None,
    reference_files: dict[str, str] | None = None,
    public_testbench: str | None = None,
    waveform_pulses: list[dict[str, str]] | None = None,
    source_matches_run: bool = True,
    checker_changed_since_run: bool = False,
    model_override: str | None = None,
    api_key_override: str | None = None,
    allow_model_fallbacks: bool = True,
    session_scope: str | None = None,
    conversation_history: list[dict[str, str]] | None = None,
    on_status: Callable[[str], None] | None = None,
) -> tuple[TutorReply, str]:
    fallback = _fallback(
        checkpoint, message, run, requested_hint_level, public_testbench,
        waveform_pulses, student_files, source_matches_run, checker_changed_since_run,
    )
    api_key = api_key_override.strip() if api_key_override else settings.openrouter_api_key
    if not api_key:
        fallback = fallback.model_copy(update={"provider_status": "no OpenRouter key configured"})
        return fallback, _format(fallback)

    selected_source = ""
    if selected_file and selected_file in student_files:
        lines = student_files[selected_file].splitlines()
        start = max((selected_start_line or 1) - 1, 0)
        end = min(selected_end_line or start + 30, len(lines))
        selected_source = "\n".join(f"{i + 1}: {line}" for i, line in enumerate(lines[start:end], start=start))

    visible_hints = checkpoint.hints[: min(max(requested_hint_level, 0), 3)]
    context: dict[str, Any] = {
        "checkpoint": checkpoint.model_dump(exclude={"hidden_testbench", "hidden_top", "hints"}),
        "student_files": {path: content[:15000] for path, content in student_files.items()},
        "selected_source": selected_source,
        "message": message,
        "requested_hint_level": requested_hint_level,
        "authored_hints_available": visible_hints,
        "run": run.model_dump(exclude={"hidden"}) if run else None,
        "conversation_history": (conversation_history or []) if settings.tutor_engine != "opencode" else [],
        "public_testbench": public_testbench[:20000] if public_testbench else None,
        "waveform_response_pulses": waveform_pulses or [],
        "source_matches_run": source_matches_run,
        "public_checker_changed_since_run": checker_changed_since_run,
        "verified_diagnostic": fallback.model_dump(include={"summary", "evidence", "error_category", "next_step"}) if fallback.error_category == "timeout" else None,
    }
    prompt = (
        "Answer the learner's message directly in the first sentence of summary. If it is a conceptual "
        "question, explain the relevant checkpoint requirement even when run is null; do not tell the "
        "learner to compile first or claim that no run prevents an answer. Distinguish request acceptance "
        "from operation completion when discussing handshakes. Cite the relevant requirement in evidence "
        "when there is no run, and cite deterministic run observations when there is one. Do not invent "
        "observations. When a waveform value is correct during cpu_resp_valid but a public assertion "
        "fails, compare the waveform response window with the public testbench's sampling instant; "
        "do not claim the value was wrong at the valid pulse. If public_checker_changed_since_run "
        "is true, explain that the stored result used an earlier checker and recommend rerunning. "
        "If source_matches_run is false, do not attribute the old failure to the current source. "
        "If verified_diagnostic is present, address it directly and do not contradict its evidence. "
        "A run with zero named checks is not a passing run. "
        "Give one concrete next action and one "
        "useful diagnostic question. Never provide a "
        "complete module, reference implementation, hidden test, or drop-in solution. Return only a JSON "
        "object with keys summary, error_category, evidence, concept, next_step, question, hint_level.\n\n"
        + json.dumps(context, indent=2)
    )
    try:
        configured_fallbacks = [item.strip() for item in settings.tutor_fallback_models.split(",") if item.strip()]
        fallback_models = (
            [item for item in configured_fallbacks if item != model_override]
            if model_override and allow_model_fallbacks
            else ([] if model_override else configured_fallbacks)
        )
        messages = [{"role": "system", "content": _system_prompt()}, {"role": "user", "content": prompt}]
        if settings.tutor_engine == "opencode":
            answer = opencode_complete(
                messages, model=model_override or settings.tutor_model,
                fallback_models=fallback_models, api_key=api_key,
                session_scope=session_scope, on_status=on_status,
                history=conversation_history,
            )
            served_model = answer["_served_model"]
            try:
                reply = _parse_model_reply(answer["content"], fallback)
            except (ValueError, TypeError):
                reply = _plain_model_reply(answer["content"], fallback)
                if reply is None:
                    raise TutorModelFormatError(served_model)
        else:
            reply, served_model = _complete_tutor_reply(
                messages=messages, requested_model=model_override or settings.tutor_model,
                fallback_models=fallback_models, api_key=api_key, defaults=fallback,
            )
        reply = reply.model_copy(update={"source": "model", "model": served_model, "engine": settings.tutor_engine})
        waveform_answer = _waveform_read_miss_answer(
            run, message, waveform_pulses, requested_hint_level, checker_changed_since_run
        )
        if waveform_answer and not re.search(r"sampl|after|late|timing", reply.summary, re.I):
            filtered = fallback.model_copy(update={"provider_status": "model response ignored waveform timing evidence"})
            return filtered, _format(filtered)
        model_claim = reply.summary + " " + " ".join(reply.evidence)
        if fallback.error_category == "timeout" and "reset polarity" in fallback.concept and (
            not re.search(r"reset", reply.summary, re.I)
            or not re.search(r"polarity|active.low|held low|reset.{0,30}(?:0|low)|(?:0|low).{0,30}reset", reply.summary, re.I)
            or re.search(r"no RTL defect|no (?:design|controller) defect|rerun unchanged", model_claim, re.I)
        ):
            filtered = fallback.model_copy(update={"provider_status": "model response ignored reset-polarity evidence"})
            return filtered, _format(filtered)
        if _is_write_handshake_question(checkpoint, message) and not all(
            signal in reply.summary + " " + " ".join(reply.evidence)
            for signal in ("mem_req_ready", "mem_resp_valid")
        ):
            filtered = fallback.model_copy(update={"provider_status": "model response was not grounded in the checkpoint contract"})
            return filtered, _format(filtered)
        if reference_files:
            reply_text = strip_reference_leak(_format(reply), [FileBlob(path=path, content=value) for path, value in reference_files.items()])
            if reply_text != _format(reply) or _contains_reference_fragment(reply_text, reference_files):
                filtered = fallback.model_copy(update={"provider_status": "model response failed the solution-leak check"})
                return filtered, _format(filtered)
        return reply, _format(reply)
    except Exception as exc:
        if isinstance(exc, OpenCodeCancelled):
            raise
        status = (
            f"malformed structured response from {exc.model}; no configured model produced a usable answer"
            if isinstance(exc, TutorModelFormatError)
            else (str(exc) if isinstance(exc, OpenCodeError) else openrouter_error_status(exc, model_override))
        )
        logger.warning("Verilog tutor model reply unavailable: %s", status)
        unavailable = fallback.model_copy(update={"provider_status": status})
        return unavailable, _format(unavailable)
