import re
from app.schemas import AssignmentArtifact, FileBlob


def clean_lines(code: str) -> list[str]:
    lines = []
    for line in code.splitlines():
        stripped = line.strip()
        # Skip empty lines and single-line comments
        if not stripped or stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("--"):
            continue
        # Normalize quotes and whitespace
        normalized = stripped.replace('"', "'")
        lines.append(normalized)
    return lines


def find_long_matching_subsequence(ref_code: str, target_code: str, min_lines: int = 5) -> bool:
    ref_lines = clean_lines(ref_code)
    target_lines = clean_lines(target_code)

    if len(ref_lines) < min_lines or len(target_lines) < min_lines:
        return False

    target_joined = "\n".join(target_lines)
    for i in range(len(ref_lines) - min_lines + 1):
        chunk = "\n".join(ref_lines[i : i + min_lines])
        if chunk in target_joined:
            return True
    return False


def assert_no_leak(artifact: AssignmentArtifact, reference_files: list[FileBlob]) -> None:
    # 1. Must contain at least one TODO in starter_files
    all_starter_content = "\n".join(f.content for f in artifact.starter_files)
    if "TODO" not in all_starter_content:
        raise ValueError("Starter code must contain at least one TODO marker.")

    # 2. Hidden test paths must not appear in starter_files
    hidden_paths = {f.path for f in artifact.hidden_tests}
    starter_paths = {f.path for f in artifact.starter_files}
    if hidden_paths.intersection(starter_paths):
        raise ValueError(f"Hidden test paths {hidden_paths.intersection(starter_paths)} found in starter files!")

    # 3. Check for reference implementation leak in starter_files, hints, or task
    combined_target = (
        all_starter_content
        + "\n"
        + "\n".join(artifact.hints)
        + "\n"
        + artifact.task
    )

    for ref in reference_files:
        if find_long_matching_subsequence(ref.content, combined_target, min_lines=5):
            raise ValueError(f"Leak detected: reference code from '{ref.path}' found in starter code, hints, or task.")


def strip_reference_leak(text: str, references: list[FileBlob]) -> str:
    target_lines = clean_lines(text)
    target_joined = "\n".join(target_lines)

    for ref in references:
        ref_lines = clean_lines(ref.content)
        if len(ref_lines) >= 3:
            for i in range(len(ref_lines) - 3 + 1):
                chunk = "\n".join(ref_lines[i : i + 3])
                if chunk in target_joined:
                    return "I cannot provide the full solution. Try focusing on the next failing assertion or reviewing the suggested approach."
    return text
