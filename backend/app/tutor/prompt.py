from pathlib import Path

PROMPT_FILE = Path("/home/ranga/opencode/tutor/backend/prompts/tutor.txt")


def get_tutor_system_prompt() -> str:
    return PROMPT_FILE.read_text(encoding="utf-8")
