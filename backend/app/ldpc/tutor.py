"""Evidence-based Python guide using the already isolated OpenCode harness."""
import ast
import json
import re
import textwrap
from pathlib import Path

from app.config import settings
from app.opencode import complete, OpenCodeCancelled, OpenCodeError
from app.verilog.schemas import TutorReply
from app.verilog.tutor import _parse_model_reply, _format


class TeachingReplyError(ValueError):
    """A safe, user-facing reason that a model answer cannot be displayed."""


def _implemented_function(code):
    try:
        tree = ast.parse(textwrap.dedent(code))
    except SyntaxError:
        # Incomplete function-shaped code is also omitted, but a bare
        # signature/comment-only interface is allowed for format questions.
        lines = code.splitlines()
        return any(re.match(r"\s*(?:return|for|while|if|[\w.\[\], ]+\s*=)\b", line)
                   for line in lines[1:]) if re.search(r"\bdef\s+\w+\s*\(", code) else False
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for statement in node.body:
            if isinstance(statement, ast.Pass):
                continue
            if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant) and (
                isinstance(statement.value.value, str) or statement.value.value is Ellipsis
            ):
                continue
            if isinstance(statement, ast.Raise) and (
                isinstance(statement.exc, ast.Name) and statement.exc.id == "NotImplementedError"
            ):
                continue
            return True
    return False


def _keep_explanation_omit_functions(text):
    """Do not throw away useful debugging prose because a model added a solution."""
    omitted = False

    def filter_block(match):
        nonlocal omitted
        if _implemented_function(match.group(2)):
            omitted = True
            return "[Complete function omitted; the explanation is kept.]"
        return match.group(0)

    text = re.sub(r"(```|~~~)[^\n]*\n(.*?)\1", filter_block, text, flags=re.S)
    # Also handle a model that writes a full function without Markdown fences.
    lines = text.splitlines(keepends=True)
    kept = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if re.match(r"^\s*(?:async\s+)?def\s+\w+\s*\(", line):
            indent = len(line) - len(line.lstrip())
            end = index + 1
            while end < len(lines) and (not lines[end].strip() or len(lines[end])-len(lines[end].lstrip()) > indent):
                end += 1
            block = "".join(lines[index:end])
            if _implemented_function(block):
                kept.append("[Complete function omitted; the explanation is kept.]\n")
                omitted = True
                index = end
                continue
        kept.append(line)
        index += 1
    cleaned = "".join(kept).strip()
    if omitted and len(cleaned.replace("[Complete function omitted; the explanation is kept.]", "").split()) < 6:
        raise TeachingReplyError("the model supplied a complete function without a useful explanation")
    return cleaned


def _format_python_reply(reply):
    """Model prose is not a place to append local fallback instructions."""
    if reply.source != "model":
        return _format(reply)
    status = f"Guide model: OpenCode · {reply.model or 'OpenRouter'}\n\n"
    parts = [reply.summary]
    # Legacy JSON responses remain supported; only model-authored fields appear.
    if reply.evidence:
        parts.append("**Basis**\n" + "\n".join(f"- {item}" for item in reply.evidence))
    for label, value in [("Concept", reply.concept), ("Next step", reply.next_step), ("Think about", reply.question)]:
        if value:
            parts.append(f"**{label}**\n{value}")
    return status + "\n\n".join(parts)


def _read_model_reply(content, fallback):
    # Never inherit authored quiz/diagnostics when a model omits a JSON field
    # or chooses a natural-language answer instead.
    neutral = fallback.model_copy(update={"summary": "", "evidence": [],
        "concept": "", "next_step": "", "question": "", "provider_status": None,
        "error_category": "unknown"})
    try:
        return _parse_model_reply(content, neutral)
    except (ValueError, TypeError):
        text = content.strip()
        if text.startswith(("{", "[", "```json")) or len(text) < 40 or len(text.split()) < 6:
            raise ValueError("No useful model answer")
        return neutral.model_copy(update={"summary": text[:12000]})


def get_python_tutor_reply(checkpoint, student_files, message, run=None, requested_hint_level=0,
    selected_file=None, selected_start_line=None, selected_end_line=None,
    reference_files=None, public_testbench=None, waveform_pulses=None,
    source_matches_run=True, checker_changed_since_run=False, model_override=None,
    api_key_override=None, allow_model_fallbacks=True, session_scope=None,
    conversation_history=None, on_status=None, theory_page=None):
    level = min(max(requested_hint_level, 0), 3)
    failures = [c for c in run.tests.cases if c.status != "pass"] if run else []
    summary = checkpoint.description
    evidence = ["Checkpoint contract: " + checkpoint.requirements[0]]
    next_step = checkpoint.hints[max(0, level-1)]
    category = "none"
    if run and not run.compile.ok:
        summary = "Python could not parse the saved source. This is a syntax failure, not an LDPC result."
        evidence = [d.message for d in run.compile.diagnostics][:2]
        category = "syntax"
    elif run and run.timed_out:
        summary = "Execution exceeded its time limit. Incomplete or zero checks do not pass."
        category = "timeout"
    elif failures:
        summary = f"The public check {failures[0].name} did not pass. Compare the expected and observed values in its assertion."
        evidence = [failures[0].message[-2500:]]
        category = "assertion"
    elif run and run.tests.passed:
        summary = f"All {run.tests.passed} public checks pass for this saved snapshot. This is public-only educational verification, not proof of full NR compliance."
    if not source_matches_run:
        evidence.append("The source has changed since this run; do not attribute its failure to the current edits.")
    fallback = TutorReply(summary=summary, error_category=category, evidence=evidence, concept=checkpoint.concepts[0], next_step=next_step, question=checkpoint.reflection or checkpoint.prediction, hint_level=level)
    if theory_page:
        fallback = TutorReply(
            summary="No live AI answer is available. Here is authored background for this page (not a tailored answer to your question):\n\n" + theory_page["sections"][0]["text"],
            error_category="none", evidence=["Theory page: " + theory_page["title"]],
            concept=theory_page["title"], next_step="Read the worked picture and remaining sections, or configure the guide model for a question-specific explanation.",
            question=theory_page["question"], hint_level=level)
    key = api_key_override.strip() if api_key_override else settings.openrouter_api_key
    if not key:
        fallback.provider_status = "no OpenRouter key configured; authored explanation/public evidence only"
        return fallback, _format(fallback)
    context = {"question": message, "checkpoint": checkpoint.model_dump(exclude={"hidden_testbench", "hidden_top", "hints"}), "files": {p: s[:15000] for p,s in student_files.items()}, "public_tests": (public_testbench or "")[:18000], "run": run.model_dump(exclude={"hidden"}) if run else None, "source_matches_run": source_matches_run, "checker_changed_since_run": checker_changed_since_run, "hints": checkpoint.hints[:level]}
    if theory_page:
        context = {"question": message, "theory_page": theory_page,
                   "learning_mode": "Beginner theory, before coding. Explain the question using this page's examples. Do not diagnose an assignment or demand tests."}
    prompt_name = "optical_flow_tutor.txt" if checkpoint.id.startswith("FLOW-") else "ldpc_tutor.txt"
    system = (Path(__file__).parents[2] / "prompts" / prompt_name).read_text(encoding="utf-8")
    try:
        requested = model_override or settings.tutor_model
        backups = [m.strip() for m in settings.tutor_fallback_models.split(",") if m.strip() and m.strip() != requested] if allow_model_fallbacks else []
        answer = complete([{"role": "system", "content": system}, {"role": "user", "content": json.dumps(context)}], requested, key, backups, session_scope, on_status, conversation_history)
        reply = _read_model_reply(answer["content"], fallback)
        reply = reply.model_copy(update={
            "summary": _keep_explanation_omit_functions(reply.summary),
            "evidence": [_keep_explanation_omit_functions(item) for item in reply.evidence],
            **{name: _keep_explanation_omit_functions(getattr(reply, name)) for name in ("concept", "next_step", "question")},
        })
        reply = reply.model_copy(update={"source": "model", "engine": "opencode", "model": answer.get("_served_model", requested)})
        return reply, _format_python_reply(reply)
    except OpenCodeCancelled:
        raise
    except Exception as error:
        fallback.provider_status = str(error) if isinstance(error, (OpenCodeError, TeachingReplyError)) else "guide response could not be read (" + type(error).__name__ + ")"
        return fallback, _format(fallback)
