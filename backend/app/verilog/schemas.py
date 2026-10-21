from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TraceSignal(StrictSchema):
    name: str
    label: str | None = None
    width: int | None = Field(default=None, ge=1, le=256)


class Checkpoint(StrictSchema):
    id: str
    title: str
    goal: str
    description: str = ""
    requirements: list[str] = Field(default_factory=list)
    module: str
    prerequisites: list[str] = Field(default_factory=list)
    source_files: list[str] = Field(min_length=1)
    editable_files: list[str] = Field(min_length=1)
    public_testbench: str
    hidden_testbench: str = ""
    top: str
    hidden_top: str | None = None
    estimated_minutes: int = Field(ge=5, le=180)
    difficulty: Literal["easy", "medium", "hard"]
    concepts: list[str] = Field(min_length=1)
    hints: list[str] = Field(min_length=3, max_length=3)
    trace_signals: list[str] = Field(default_factory=list)
    compile_testbench: str | None = None
    lesson: str = ""
    input_reference: str = ""
    visual: str = ""
    prediction: str = ""
    reflection: str = ""
    expected_public_checks: int = 0
    fixture: dict[str, Any] = Field(default_factory=dict)
    experiment: str = ""
    optional_math: str = ""
    optional_hardware: str = ""
    takeaway: str = ""
    completion: str = ""
    misconception: str = ""


class CourseManifest(StrictSchema):
    schema_version: int = 1
    id: str
    title: str
    subtitle: str = ""
    toolchain: Literal["iverilog", "python"] = "iverilog"
    overview_file: str
    architecture_file: str
    provided_files: list[str] = Field(default_factory=list)
    checkpoints: list[Checkpoint] = Field(min_length=1)


class Diagnostic(StrictSchema):
    severity: Literal["error", "warning", "info"] = "error"
    category: Literal["syntax", "elaboration", "simulation", "infrastructure", "unknown"] = "unknown"
    message: str
    file: str | None = None
    line: int | None = Field(default=None, ge=1)
    column: int | None = Field(default=None, ge=1)


class TestCaseResult(StrictSchema):
    name: str
    status: Literal["pass", "fail", "error"]
    message: str = ""


class TraceEvent(StrictSchema):
    values: dict[str, str] = Field(default_factory=dict)


class TestSummary(StrictSchema):
    passed: int = 0
    failed: int = 0
    errors: int = 0
    cases: list[TestCaseResult] = Field(default_factory=list)


class CompileSummary(StrictSchema):
    ok: bool
    diagnostics: list[Diagnostic] = Field(default_factory=list)


class RunArtifact(StrictSchema):
    name: str
    kind: Literal["waveform", "trace", "log"]
    url: str | None = None


class LabRunResult(StrictSchema):
    stage: Literal["compile", "elaboration", "simulation", "infrastructure"]
    compile: CompileSummary
    tests: TestSummary = Field(default_factory=TestSummary)
    hidden: TestSummary | None = None
    timed_out: bool = False
    runtime_ms: int = 0
    passed: bool = False
    diagnostics: list[Diagnostic] = Field(default_factory=list)
    traces: list[TraceEvent] = Field(default_factory=list)
    artifacts: list[RunArtifact] = Field(default_factory=list)
    output: str = ""


class LabRunRequest(StrictSchema):
    checkpoint_id: str
    mode: Literal["compile", "test", "submit"] = "test"


class FileUpdate(StrictSchema):
    content: str = Field(max_length=262144)


class TutorRequest(StrictSchema):
    checkpoint_id: str
    theory_page_id: str | None = Field(default=None, max_length=80)
    message: str = Field(min_length=1, max_length=8000)
    run_id: str | None = None
    requested_hint_level: int = Field(default=0, ge=0, le=3)
    selected_file: str | None = None
    selected_start_line: int | None = Field(default=None, ge=1)
    selected_end_line: int | None = Field(default=None, ge=1)
    model: str | None = Field(default=None, min_length=1, max_length=160, pattern=r"^[A-Za-z0-9._:/-]+$")
    allow_model_fallbacks: bool = True


class TutorReply(StrictSchema):
    summary: str
    error_category: Literal["syntax", "elaboration", "protocol", "state", "assertion", "timeout", "integration", "none", "unknown"]
    evidence: list[str] = Field(default_factory=list, max_length=5)
    concept: str
    next_step: str
    question: str
    hint_level: int = Field(ge=0, le=3)
    source: Literal["model", "fallback"] = "fallback"
    model: str | None = None
    provider_status: str | None = None
    engine: str | None = None


class LabMessageResponse(StrictSchema):
    id: str
    role: Literal["user", "assistant"]
    content: str
    hint_level: int = 0
    run_id: str | None = None
    created_at: str


class CheckpointProgress(StrictSchema):
    id: str
    title: str
    goal: str
    status: Literal["locked", "available", "in_progress", "passed"]
    estimated_minutes: int
    difficulty: str
    concepts: list[str]


class LabSessionResponse(StrictSchema):
    id: str
    course_id: str
    learner_key: str
    passed_checkpoint_ids: list[str]
    checkpoints: list[CheckpointProgress]
    created_at: str
    updated_at: str


class TheorySection(StrictSchema):
    title: str
    text: str
    visual: Literal["correspondence", "patch", "ambiguity", "sampling", "alignment", "refinement", "pyramid", "evaluation", "consistency"] | None = None


class TheoryConnection(StrictSchema):
    id: str
    why: str


class TheoryPage(StrictSchema):
    id: str
    title: str
    goal: str
    diagram: Literal["channel", "repetition", "parity", "graph", "decoding", "hardware", "flow"]
    sections: list[TheorySection]
    optional_sections: list[TheorySection] = Field(default_factory=list)
    question: str
    answer: str
    connections: list[TheoryConnection]
    fixture: dict[str, Any] = Field(default_factory=dict)


class CourseResponse(StrictSchema):
    manifest: CourseManifest
    overview: str
    architecture: str
    theory_pages: list[TheoryPage] = Field(default_factory=list)
    session_id: str | None = None
    progress: list[CheckpointProgress] = Field(default_factory=list)


class AnyDict(StrictSchema):
    value: dict[str, Any]
