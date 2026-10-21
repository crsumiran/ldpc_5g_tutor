from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field

LearnerLevel = Literal["python_comfortable"]
PlanStatus = Literal["draft", "approved"]
Difficulty = Literal["easy", "medium", "hard"]
AdapterKind = Literal["python_pytest", "sql_duckdb", "dbt", "pyspark", "plan_only"]
ComponentKind = Literal["pipeline", "model", "schema", "test", "ingest", "transform", "serve", "other"]
JobStatus = Literal["queued", "running", "done", "error"]
JobKind = Literal["analyze", "generate_plan", "generate_assignments", "evaluate"]


class BaseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Component(BaseSchema):
    name: str
    kind: ComponentKind
    paths: list[str] = Field(default_factory=list)
    summary: str


class DataFlow(BaseSchema):
    source: str
    sink: str
    paths: list[str] = Field(default_factory=list)
    summary: str


class DevCommand(BaseSchema):
    name: str
    command: list[str]


class ImportantFile(BaseSchema):
    path: str
    reason: str
    bytes: int


class RepositoryAnalysis(BaseSchema):
    project_summary: str
    stack: list[str]
    components: list[Component] = Field(default_factory=list)
    data_flows: list[DataFlow] = Field(default_factory=list)
    development_commands: list[DevCommand] = Field(default_factory=list)
    important_files: list[ImportantFile] = Field(default_factory=list)
    detected_adapters: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)


class PlanAssignment(BaseSchema):
    id: str
    title: str
    prerequisites: list[str] = Field(default_factory=list)
    concepts: list[str] = Field(default_factory=list)
    source_files: list[str] = Field(default_factory=list)
    estimated_minutes: int = 45
    difficulty: Difficulty = "medium"
    adapter: AdapterKind = "plan_only"


class LearningPlan(BaseSchema):
    title: str
    learner_level: LearnerLevel = "python_comfortable"
    status: PlanStatus = "draft"
    assignments: list[PlanAssignment] = Field(default_factory=list)


class FileBlob(BaseSchema):
    path: str
    content: str


class RubricItem(BaseSchema):
    name: str
    weight: float


class AssignmentArtifact(BaseSchema):
    id: str
    title: str
    business_context: str
    objectives: list[str]
    concepts: list[str]
    inspect_files: list[str]
    task: str
    approach: list[str]
    starter_files: list[FileBlob]
    public_tests: list[FileBlob]
    hidden_tests: list[FileBlob] = Field(default_factory=list)
    run_command: list[str]
    hints: list[str]
    rubric: list[RubricItem]
    acceptance: list[str]
    estimated_minutes: int
    adapter: AdapterKind


class TestCounts(BaseSchema):
    passed: int = 0
    failed: int = 0
    errors: int = 0
    output: str = ""


class LintResult(BaseSchema):
    ok: bool = True
    output: str = ""


class Evaluation(BaseSchema):
    setup_ok: bool = True
    syntax_ok: bool = True
    public: TestCounts = Field(default_factory=TestCounts)
    hidden: TestCounts = Field(default_factory=TestCounts)
    lint: LintResult = Field(default_factory=LintResult)
    timed_out: bool = False
    runtime_ms: int = 0
    passed: bool = False
    rubric_scores: dict[str, float] = Field(default_factory=dict)


class ChatRequest(BaseSchema):
    assignment_id: str | None = None
    lesson_id: str | None = None
    message: str
    code: str | None = None
    history: list[dict[str, Any]] = Field(default_factory=list)


class ChatResponse(BaseSchema):
    reply: str
    passed: bool = False
    evaluation: Evaluation | None = None
    executor_output: str | None = None


class JobResponse(BaseSchema):
    id: str
    kind: str
    status: JobStatus
    error: str | None = None
    result_json: dict[str, Any] | None = None
