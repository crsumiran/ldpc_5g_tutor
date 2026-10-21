from pathlib import Path

from app.executor import run_verilog
from app.llm import TOOLS, complete, describe_image
from app.models import ChatRequest, ChatResponse

PROMPT_PATH = Path("/home/ranga/opencode/tutor/backend/prompts/tutor.txt")


def _system() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def handle_chat(req: ChatRequest) -> ChatResponse:
    messages: list[dict] = [{"role": "system", "content": _system()}]
    messages.extend(req.history)
    user = req.message
    if req.image:
        transcript = describe_image(req.image)
        user += f"\n\n<image_transcript>\n{transcript}\n</image_transcript>"
    if req.code:
        user += f"\n\n<student_code lesson=\"{req.lesson_id}\">\n{req.code}\n</student_code>"
    messages.append({"role": "user", "content": user})

    last_exec = None
    passed = False
    for _ in range(3):
        msg = complete(messages, tools=TOOLS)
        tool_calls = msg.get("tool_calls") or []
        if not tool_calls:
            return ChatResponse(
                reply=msg.get("content") or "",
                passed=passed,
                executor_output=last_exec,
            )
        messages.append(msg)
        for call in tool_calls:
            fn = call["function"]
            args = fn.get("arguments") or "{}"
            if isinstance(args, str):
                import json
                args = json.loads(args)
            result = run_verilog(args.get("lesson_id", req.lesson_id), args.get("code", req.code or ""))
            last_exec = (result.stdout + "\n" + result.stderr).strip()
            passed = result.passed
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "content": last_exec or f"exit={result.exit_code}",
                }
            )
    return ChatResponse(reply="I could not finish checking your code. Try again.", passed=passed, executor_output=last_exec)