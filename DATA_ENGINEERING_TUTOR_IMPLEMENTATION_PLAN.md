# Data Engineering Tutor — Small-Model Implementation Plan

Feed the implementing model **one TASK at a time**. Do not let it choose frameworks, invent APIs, or skip verification.

This document is the source of truth. Do not reopen locked decisions. Do not implement Verilog. Do not modify `IMPLEMENTATION_PLAN.md`.

Operator prompt template:

```
Read /home/ranga/opencode/tutor/DATA_ENGINEERING_TUTOR_IMPLEMENTATION_PLAN.md
Do ONLY TASK NN. Do not start any other task.
```

If a step is already done, skip it. Check the **VERIFY** block first.

---

## Product

Train a Python-comfortable learner (the wife) on data engineering by feeding a real project.

Two planning modes:

1. **AI-generated plan.** The model reads an imported project, understands its architecture, and proposes a dependency-ordered assignment DAG.
2. **Mentor-authored plan.** The operator selects files or features and defines what the learner should implement. The system compiles that into a CS231n-style assignment.

Typical loop:

1. Import a project from a local directory, Git URL, or ZIP.
2. Analyze the repository without executing it.
3. Detect languages, frameworks, pipelines, schemas, tests, and development commands.
4. Generate a repository map and architectural explanation.
5. Propose a learning plan for a Python-comfortable learner.
6. Mentor reviews, reorders, edits, removes, or adds assignments.
7. Generate an isolated learner workspace.
8. Replace selected implementation sections with a partial algorithm and TODO blocks.
9. Give the learner:
   - Problem description
   - Relevant data-engineering concepts
   - Files to inspect
   - Suggested approach
   - Starter code with a partial algorithm
   - Public tests
   - Run command
   - Progressive hints
10. Keep the original implementation and hidden tests unavailable to the learner.
11. Run submissions in a sandbox.
12. Provide Socratic feedback without revealing the completed implementation.
13. Track progress and unlock dependent assignments.

Example assignment style (partial algorithm — this is the required scaffolding density):

```python
def normalize_orders(orders: pd.DataFrame) -> pd.DataFrame:
    """Return validated orders in the canonical order schema."""

    # Step 1: Create a copy so the input frame is not modified.
    normalized = orders.copy()

    # Step 2: Convert order timestamps to UTC.
    # TODO: Implement timestamp parsing and timezone normalization.

    # Step 3: Remove records that do not have a valid order identifier.
    # TODO: Implement identifier validation.

    # Step 4: Return columns in the order required by ORDER_SCHEMA.
    raise NotImplementedError
```

The learner gets enough structure to begin, but not the completed transformation.

---

## Locked decisions (do not reopen)

| Decision | Choice | Why |
|---|---|---|
| Domain | Data engineering tutor. Not Verilog. | Operator request. |
| Learner level | Python-comfortable. Teach SQL, schemas, transformations, pipelines, tests. | Chosen. |
| Assignment style | Partial algorithm: ordered steps + some setup code + unfinished transformations. | Chosen. |
| Project input | Local path **and** Git URL **and** ZIP upload. | Chosen. |
| Stack detection | Broad project-native analysis. | Chosen. |
| Executable grading | Only through adapters. Unsupported stacks stay plan-only. | Safety. |
| MVP adapters | Python/`pytest`, then SQL/DuckDB. dbt and PySpark after MVP. | Ship the loop first. |
| Framework | Plain Python + FastAPI. **Not** AutoGen. **Not** OpenHands. | Smaller model can write this. |
| Jobs | In-process FastAPI `BackgroundTasks` + SQLite job rows. No Redis/Celery in MVP. | Fewer moving parts. |
| DB | SQLite via SQLAlchemy 2 + Alembic. | Single-file, testable. |
| Brain | OpenRouter via `OPENROUTER_API_KEY`. Model from env `TUTOR_MODEL` default `openai/gpt-4o-mini`. Planner may use `PLANNER_MODEL` defaulting to the same. | Swap later. |
| Evaluator | Deterministic. LLM never decides pass/fail. | Honesty. |
| Sandbox | Docker, no network, memory/CPU/time limits, read-only root, dropped caps. | Untrusted student code. |
| Frontend | Static HTML mentor + learner views in `web/`. **Not** Next.js yet. | Defer SPA. |
| Python | 3.11+ | |
| Workdir | `/home/ranga/opencode/tutor` | Never write outside this tree except Docker image build. |
| Data dir | `/home/ranga/opencode/tutor/data` | Snapshots, workspaces, SQLite. |

Do not send an entire large repository in one model call. Pipeline is:

```
Repository
  -> deterministic inventory
  -> prioritized file selection
  -> component summaries with path citations
  -> project architecture summary
  -> learning-plan generation
  -> human review
  -> assignment generation
```

---

## How a small model must work

1. Read only the TASK you were given.
2. Run every COMMAND in order.
3. Write files exactly as specified. Do not add comments, extras, or refactors.
4. Run VERIFY. If it fails, fix only that TASK. Do not start the next TASK.
5. Stop. Reply with: `TASK NN DONE` or `TASK NN FAILED: <one line>`.

Never:

- Execute imported project code during analysis.
- Mount `reference/` or hidden tests into the learner workspace.
- Put secrets, Git credentials, or `.env` files into LLM prompts.
- Let the tutor emit a complete drop-in solution.
- Claim a project is auto-gradable unless an adapter `detect()` returns true.

---

## Target tree (create only these paths, over tasks)

```
/home/ranga/opencode/tutor/
  DATA_ENGINEERING_TUTOR_IMPLEMENTATION_PLAN.md   (this file — do not modify)
  IMPLEMENTATION_PLAN.md                          (Verilog plan — do not modify)
  opensource_tutor_strategy.md
  .env.example
  .gitignore
  docker-compose.yml
  sandbox/
    Dockerfile
    entrypoint.sh
  backend/
    alembic.ini
    alembic/
      env.py
      versions/
    requirements.txt
    app/
      __init__.py
      main.py
      config.py
      db.py
      models.py                 # SQLAlchemy tables
      schemas.py                # Pydantic API + LLM JSON schemas
      jobs.py
      security.py
      llm.py
      ingest/
        __init__.py
        local.py
        git.py
        zip.py
        snapshot.py
      analysis/
        __init__.py
        inventory.py
        stack.py
        select.py
        llm_analyze.py
      planning/
        __init__.py
        generate.py
        validate.py
        manual.py
      assignments/
        __init__.py
        compile.py
        workspace.py
        leakcheck.py
      adapters/
        __init__.py
        base.py
        python_pytest.py
        sql_duckdb.py
        dbt.py                  # TASK 14 only
        pyspark.py              # TASK 14 only
      eval/
        __init__.py
        sandbox.py
        evaluate.py
      tutor/
        __init__.py
        prompt.py
        chat.py
      api/
        __init__.py
        projects.py
        plans.py
        assignments.py
        submissions.py
        progress.py
    prompts/
      analyst.txt
      planner.txt
      assignment_compiler.txt
      tutor.txt
  web/
    index.html                  # mentor home
    mentor.html
    learner.html
    app.js
    styles.css
  tests/
    conftest.py
    test_schemas.py
    test_storage.py
    test_ingestion.py
    test_repository_analyzer.py
    test_llm_analysis.py
    test_planner.py
    test_plan_api.py
    test_assignment_compiler.py
    test_workspace.py
    test_adapters.py
    test_evaluator.py
    test_sandbox_security.py
    test_tutor.py
    test_api_workflow.py
    e2e/
      test_python_etl.py
      test_duckdb_pipeline.py
  fixtures/
    python_etl/
    duckdb_pipeline/
    zip_traversal/
    bad_symlink/
  data/                         # gitignored runtime
```

---

## Frozen JSON contracts

Implement these Pydantic models in `backend/app/schemas.py`. Field names are frozen.

### RepositoryAnalysis

```json
{
  "project_summary": "string",
  "stack": ["Python", "pytest"],
  "components": [
    {
      "name": "string",
      "kind": "pipeline|model|schema|test|ingest|transform|serve|other",
      "paths": ["src/orders/validation.py"],
      "summary": "string"
    }
  ],
  "data_flows": [
    {
      "source": "string",
      "sink": "string",
      "paths": ["src/pipeline.py"],
      "summary": "string"
    }
  ],
  "development_commands": [
    {"name": "test", "command": ["pytest", "-q"]}
  ],
  "important_files": [
    {"path": "src/orders/validation.py", "reason": "core transform", "bytes": 1200}
  ],
  "detected_adapters": ["python_pytest"],
  "risks": ["string"],
  "unknowns": ["string"]
}
```

Every `paths` / `path` value must exist in the snapshot. The LLM analyst must cite paths; the validator drops or rejects invented paths.

### LearningPlan

```json
{
  "title": "string",
  "learner_level": "python_comfortable",
  "status": "draft|approved",
  "assignments": [
    {
      "id": "DE-001",
      "title": "Validate raw order records",
      "prerequisites": [],
      "concepts": ["schema validation", "null handling"],
      "source_files": ["src/orders/validation.py"],
      "estimated_minutes": 45,
      "difficulty": "easy|medium|hard",
      "adapter": "python_pytest|sql_duckdb|plan_only"
    }
  ]
}
```

Rules:

- `id` unique, `DE-` prefix plus three digits.
- `prerequisites` must refer to earlier IDs. No cycles.
- `source_files` must exist.
- `adapter` is `plan_only` unless a registered adapter `detect()`s the snapshot.

### AssignmentArtifact

```json
{
  "id": "DE-001",
  "title": "string",
  "business_context": "string",
  "objectives": ["string"],
  "concepts": ["string"],
  "inspect_files": ["path"],
  "task": "string",
  "approach": ["Step 1: ...", "Step 2: ..."],
  "starter_files": [{"path": "src/foo.py", "content": "..."}],
  "public_tests": [{"path": "tests/test_foo.py", "content": "..."}],
  "hidden_tests": [{"path": "hidden/test_foo_hidden.py", "content": "..."}],
  "run_command": ["pytest", "tests/test_foo.py", "-q"],
  "hints": ["level1", "level2", "level3"],
  "rubric": [{"name": "correctness", "weight": 0.7}, {"name": "cleanliness", "weight": 0.3}],
  "acceptance": ["public tests pass", "hidden tests pass"],
  "estimated_minutes": 45,
  "adapter": "python_pytest"
}
```

Leak rules for learner-visible payloads:

- Must not contain the reference implementation.
- Must not contain `hidden_tests`.
- Must not contain answers in comments.
- Starter code must include at least one `TODO` and one `raise NotImplementedError` or equivalent incomplete step.

### Evaluation

```json
{
  "setup_ok": true,
  "syntax_ok": true,
  "public": {"passed": 3, "failed": 1, "errors": 0, "output": "..."},
  "hidden": {"passed": 0, "failed": 2, "errors": 0, "output": "..."},
  "lint": {"ok": true, "output": ""},
  "timed_out": false,
  "runtime_ms": 812,
  "passed": false,
  "rubric_scores": {"correctness": 0.4, "cleanliness": 0.8}
}
```

`passed` is true only if setup, syntax, public, and hidden all succeed and `timed_out` is false.

---

## Frozen prompts

Write these **exactly**. Do not paraphrase.

### `backend/prompts/analyst.txt`

```
You are a data-engineering repository analyst. You receive a deterministic file inventory and selected file excerpts. You never execute code.

Return only valid JSON matching RepositoryAnalysis. Every path you mention must appear in the inventory. If you are unsure, put the question in "unknowns". Do not invent files, commands, or adapters. detected_adapters may only use: python_pytest, sql_duckdb, dbt, pyspark.
```

### `backend/prompts/planner.txt`

```
You are a curriculum planner for a Python-comfortable adult learning data engineering from a real project.

Input: RepositoryAnalysis JSON plus optional mentor notes.
Output: only valid JSON matching LearningPlan with status "draft".

Rules:
1. Order assignments as a DAG of increasing dependency.
2. Each assignment teaches one coherent skill (schema, transform, test, join, pipeline step).
3. source_files must come from the analysis.
4. Prefer adapter python_pytest or sql_duckdb when detected; otherwise adapter plan_only.
5. Do not generate assignment source code here.
6. Estimated minutes between 20 and 90.
7. IDs are DE-001, DE-002, ...
```

### `backend/prompts/assignment_compiler.txt`

```
You compile one LearningPlan assignment into a CS231n-style data-engineering exercise.

Input: the plan item, cited source files, and the reference implementation excerpts.
Output: only valid JSON matching AssignmentArtifact.

Style: partial algorithm. Provide numbered approach steps and starter code that includes setup plus TODO blocks. Leave the meaningful transformation unfinished with raise NotImplementedError.

Rules:
1. Never include the full correct transformation in starter_files, hints, task, or comments.
2. Public tests should fail on the starter and pass on the reference.
3. Hidden tests cover edge cases not stated in public tests.
4. inspect_files and starter paths must be paths from the snapshot.
5. Exactly three hints, increasing specificity, still not a full solution.
6. run_command must be a JSON array of strings.
```

### `backend/prompts/tutor.txt`

```
You are an expert data engineer and a Socratic tutor. Your goal is to help the learner implement the current assignment without giving the final solution.

# Rules
1. Never write the complete correct implementation.
2. Never paste hidden tests or reference code.
3. When the learner submits code, you will be given a deterministic Evaluation JSON. Use it. Do not claim tests passed unless evaluation.passed is true.
4. Explain concepts (schemas, nulls, joins, idempotency, late data) and point to concrete files and failing assertions.
5. Give only the next hint level when asked. There are three levels.
6. Do not unlock or discuss the next assignment until evaluation.passed is true.
7. Conceptual questions may be answered without code.
8. Tone: encouraging, pedagogical, technical.
```

---

## Security model (implement in TASK 00 notes + TASK 02/10)

Write `docs/security-model.md` in TASK 00 with these rules, then enforce them in code:

1. Local import roots: only paths under `ALLOWED_IMPORT_ROOTS` (env, default `/home/ranga/opencode`).
2. ZIP: reject absolute paths, `..`, overwrites outside dest, files > 5 MiB, total uncompressed > 50 MiB.
3. Git: `git clone --depth 1 --single-branch --recurse-submodules=no`. Do not copy `.git` hooks into the snapshot. Strip `.git` after clone.
4. Symlinks in snapshots: refuse if target is outside the snapshot.
5. Analysis never runs project code, `setup.py`, or Makefile.
6. Secrets: skip files named `.env`, `.env.*`, `id_rsa`, `*.pem`, `credentials.json` from LLM excerpts.
7. Sandbox: `network_disabled=True`, `cap_drop=["ALL"]`, `read_only=True`, `no-new-privileges`, mem `512m`, cpus `1.0`, timeout 30s, tmpfs `/tmp` and `/work`.
8. Learner mounts: workspace only. Never `reference/`, never hidden tests as writable files. Hidden tests mount read-only at `/hidden` only inside the evaluator container.
9. LLM prompts get excerpts capped at 80k characters total, selected by `analysis/select.py`.

---

## API shape (implement in TASK 12; stub health in TASK 05)

```
GET  /api/health

POST /api/projects/local          { "path": "..." }
POST /api/projects/git            { "url": "..." }
POST /api/projects/upload         multipart file
GET  /api/projects
GET  /api/projects/{id}
POST /api/projects/{id}/analyze
GET  /api/projects/{id}/analysis
GET  /api/jobs/{id}

POST /api/projects/{id}/plans/generate   { "notes": "optional" }
POST /api/projects/{id}/plans/manual     { LearningPlan }
GET  /api/plans/{id}
PATCH /api/plans/{id}
POST /api/plans/{id}/approve

POST /api/plans/{id}/assignments/generate
GET  /api/assignments/{id}
PATCH /api/assignments/{id}
POST /api/assignments/{id}/publish

POST /api/assignments/{id}/workspace
POST /api/assignments/{id}/submissions   { "message": "...", "files": optional }
GET  /api/submissions/{id}/evaluation
POST /api/assignments/{id}/chat          { "message": "...", "code": optional, "history": [] }

GET  /api/progress
```

Long work (analyze, generate plan, generate assignments, evaluate) creates a `jobs` row and returns `{ "job_id": "..." }`. Poll `GET /api/jobs/{id}` until `status=done|error`.

---

## Data layout per project

```
data/projects/<project-id>/
  source/                 # immutable snapshot
  analysis/analysis.json
  plans/<plan-id>.json
  reference/<assignment-id>/   # instructor only
  learner/<workspace-id>/      # learner mount
```

SQLite file: `data/tutor.db`.

---

# TASK 00 — Prerequisites, gitignore, security doc, frozen prompts

## COMMANDS

```bash
python3 --version
docker --version
docker info >/dev/null
test -n "$OPENROUTER_API_KEY" && echo KEY_SET || echo KEY_MISSING
mkdir -p /home/ranga/opencode/tutor/{sandbox,backend/app/{ingest,analysis,planning,assignments,adapters,eval,tutor,api},backend/prompts,backend/alembic/versions,web,tests/e2e,fixtures/{python_etl,duckdb_pipeline,zip_traversal,bad_symlink},docs,data}
```

`python3` must be 3.11+. `docker info` must succeed. `KEY_MISSING` is OK until TASK 13.

## FILES

Create `/home/ranga/opencode/tutor/.gitignore` if missing; ensure it contains:

```
.env
__pycache__/
*.pyc
.venv/
node_modules/
*.vcd
data/
```

Create `/home/ranga/opencode/tutor/.env.example`:

```
OPENROUTER_API_KEY=
TUTOR_MODEL=openai/gpt-4o-mini
PLANNER_MODEL=openai/gpt-4o-mini
SANDBOX_IMAGE=de-tutor-sandbox:latest
SANDBOX_TIMEOUT_SEC=30
SANDBOX_MEM=512m
API_HOST=0.0.0.0
API_PORT=8000
DATABASE_URL=sqlite:////home/ranga/opencode/tutor/data/tutor.db
ALLOWED_IMPORT_ROOTS=/home/ranga/opencode
DATA_DIR=/home/ranga/opencode/tutor/data
```

Write the four frozen prompts from this document to:

- `backend/prompts/analyst.txt`
- `backend/prompts/planner.txt`
- `backend/prompts/assignment_compiler.txt`
- `backend/prompts/tutor.txt`

Write `docs/security-model.md` with the nine rules from the Security model section, copied faithfully.

Create empty `__init__.py` in every `backend/app` package listed in the tree.

## VERIFY

```bash
test -f /home/ranga/opencode/tutor/backend/prompts/tutor.txt
grep -q "Never write the complete correct implementation" /home/ranga/opencode/tutor/backend/prompts/tutor.txt
test -f /home/ranga/opencode/tutor/docs/security-model.md
test -d /home/ranga/opencode/tutor/backend/app/ingest
```

---

# TASK 01 — Python env, config, schemas

## FILES

Create `/home/ranga/opencode/tutor/backend/requirements.txt`:

```
fastapi==0.115.6
uvicorn==0.34.0
httpx==0.28.1
pydantic==2.10.4
pydantic-settings==2.7.1
sqlalchemy==2.0.36
alembic==1.14.0
docker==7.1.0
pytest==8.3.4
python-multipart==0.0.20
```

Create `/home/ranga/opencode/tutor/backend/app/config.py` using `pydantic-settings` with the env vars from `.env.example`. Defaults must match `.env.example`.

Create `/home/ranga/opencode/tutor/backend/app/schemas.py` with Pydantic models for:

- `RepositoryAnalysis` and nested types
- `LearningPlan`, `PlanAssignment`
- `AssignmentArtifact`, `FileBlob`, `RubricItem`
- `Evaluation`, `TestCounts`
- `ChatRequest`, `ChatResponse`
- `JobStatus`

Enums: `learner_level` only `python_comfortable` in MVP; `adapter` in `python_pytest | sql_duckdb | dbt | pyspark | plan_only`; `plan status` `draft | approved`; `job status` `queued | running | done | error`.

Create `/home/ranga/opencode/tutor/tests/test_schemas.py` that:

- Parses a minimal valid `LearningPlan` JSON.
- Rejects a cycle: DE-001 prereq DE-002, DE-002 prereq DE-001 — this cycle check may live in planning validation later; for TASK 01 only test Pydantic required fields and extra-forbid.
- Rejects missing `title`.

Use `model_config = ConfigDict(extra="forbid")` on all these models.

## COMMANDS

```bash
python3 -m venv /home/ranga/opencode/tutor/.venv
/home/ranga/opencode/tutor/.venv/bin/pip install -r /home/ranga/opencode/tutor/backend/requirements.txt
cd /home/ranga/opencode/tutor/backend && PYTHONPATH=/home/ranga/opencode/tutor/backend /home/ranga/opencode/tutor/.venv/bin/python -m pytest /home/ranga/opencode/tutor/tests/test_schemas.py -q
```

## VERIFY

`pytest` shows passed. Import: `from app.schemas import LearningPlan, RepositoryAnalysis, AssignmentArtifact, Evaluation`.

---

# TASK 02 — SQLite models + Alembic

## FILES

`backend/app/models.py` SQLAlchemy 2 tables:

- `projects(id, source_type, source_uri, snapshot_hash, snapshot_path, created_at)`
- `analyses(id, project_id, json, created_at)`
- `plans(id, project_id, json, status, created_at, updated_at)`
- `assignments(id, plan_id, artifact_json, published, created_at)`
- `workspaces(id, assignment_id, path, created_at)`
- `submissions(id, workspace_id, evaluation_json, created_at)`
- `conversations(id, assignment_id, json, updated_at)`
- `progress(id, assignment_id, passed, updated_at)`
- `jobs(id, kind, status, error, result_json, created_at, updated_at)`

IDs are UUID strings.

`backend/app/db.py`: engine from `settings.database_url`, `SessionLocal`, `get_db`.

Alembic initial revision creating all tables.

`tests/test_storage.py`: create a project row, commit, read back.

## COMMANDS

```bash
cd /home/ranga/opencode/tutor/backend
PYTHONPATH=/home/ranga/opencode/tutor/backend /home/ranga/opencode/tutor/.venv/bin/alembic upgrade head
PYTHONPATH=/home/ranga/opencode/tutor/backend /home/ranga/opencode/tutor/.venv/bin/python -m pytest /home/ranga/opencode/tutor/tests/test_storage.py -q
```

If Alembic is not configured, write `alembic.ini` with `script_location = alembic` and `sqlalchemy.url` unused (read URL from app config in `alembic/env.py`).

## VERIFY

`data/tutor.db` exists after upgrade. Storage test passed.

---

# TASK 03 — Project ingestion (local, git, zip)

## FILES

`app/ingest/snapshot.py`

- `new_project_id() -> str`
- `snapshot_dir(project_id) -> Path`
- `hash_tree(path) -> str` SHA256 of sorted relative paths + file hashes
- `refuse_symlink_escape(root: Path) -> None`

`app/ingest/local.py`

- Copy tree from `path` into `source/` if `path` is under one of `ALLOWED_IMPORT_ROOTS`.
- Exclude `.git`, `__pycache__`, `.venv`, `node_modules`.

`app/ingest/git.py`

- Run `git clone --depth 1 --single-branch --recurse-submodules=no <url> <tmp>`
- Then copy working tree without `.git`.

`app/ingest/zip.py`

- Safe extract: no absolute names, no `..`, size caps from security model.

Public function `ingest_project(kind, **kwargs) -> project_id` writes DB row.

## TESTS `tests/test_ingestion.py`

1. Local copy of `fixtures/python_etl` succeeds and hash is stable if run twice on same files.
2. Path outside allowed roots raises.
3. ZIP with `../evil.py` raises and writes nothing under `data/`.
4. ZIP with absolute path raises.
5. Git clone is tested with a local `git init` fixture repo, not the network. Skip if `git` missing.

## COMMANDS

Create a tiny `fixtures/python_etl` if empty (TASK 03 may add a `README.md` and `src/hello.py` only; TASK 08 replaces with the real fixture).

```bash
PYTHONPATH=/home/ranga/opencode/tutor/backend /home/ranga/opencode/tutor/.venv/bin/python -m pytest /home/ranga/opencode/tutor/tests/test_ingestion.py -q
```

## VERIFY

All ingestion tests passed. No files outside `data/projects/`.

---

# TASK 04 — Deterministic repository analysis

## FILES

`app/analysis/inventory.py`

- Walk snapshot. Record relative path, bytes, suffix.
- Skip binary files over 256 KiB for later excerpting; still list them.

`app/analysis/stack.py`

- Detect from filenames/manifests:
  - `pyproject.toml` / `requirements.txt` / `*.py` → Python
  - `test_*.py` / `pytest` dep → pytest
  - `*.sql`, `duckdb` dep → SQL/DuckDB
  - `dbt_project.yml` → dbt
  - `pyspark` / `SparkSession` → PySpark
  - `airflow` / `dagster` / `prefect` as stack labels only
- `detected_adapters`: `python_pytest` if pytest-like tests exist; `sql_duckdb` if `.sql` files and no dbt; others only if their marker files exist.

`app/analysis/select.py`

- Rank files: README, manifests, `src/**/*.py`, `models/**/*.sql`, tests.
- Return excerpts totaling ≤ 80k chars. Skip secret filenames.

`analyze_deterministic(snapshot: Path) -> dict` returns inventory + stack + selected files, no LLM.

## TESTS

`tests/test_repository_analyzer.py` uses `fixtures/python_etl` and `fixtures/duckdb_pipeline` (create minimal trees here if TASK 08 has not run: a `pytest` project and a folder of `.sql` files).

Assert adapter detection and that `.env` is not selected.

## VERIFY

```bash
PYTHONPATH=/home/ranga/opencode/tutor/backend /home/ranga/opencode/tutor/.venv/bin/python -m pytest /home/ranga/opencode/tutor/tests/test_repository_analyzer.py -q
```

---

# TASK 05 — LLM client + analyst (mocked)

## FILES

`app/llm.py`

- `complete(messages, model=None) -> dict` POST OpenRouter chat completions, `temperature=0.2`, `response_format={"type":"json_object"}` when JSON is required.
- `complete_json(messages, model=None) -> dict` parse JSON or raise.

`app/analysis/llm_analyze.py`

- Load `prompts/analyst.txt`.
- Send inventory summary + excerpts.
- Validate as `RepositoryAnalysis`.
- Drop any cited path not in inventory.
- If `detected_adapters` contains unknown values, replace with deterministic stack.py result.

`app/jobs.py`: `create_job`, `run_job(kind, fn)`, status updates.

`app/main.py`: FastAPI app, CORS `*`, `GET /api/health` → `{"ok": true}`.

## TESTS

`tests/test_llm_analysis.py` monkeypatches `complete_json` to return a fixture analysis with one invented path; assert the invented path is stripped.

## VERIFY

```bash
PYTHONPATH=/home/ranga/opencode/tutor/backend /home/ranga/opencode/tutor/.venv/bin/python -m pytest /home/ranga/opencode/tutor/tests/test_llm_analysis.py /home/ranga/opencode/tutor/tests/test_schemas.py -q
```

Health: import app and `TestClient.get("/api/health")` is 200.

---

# TASK 06 — Curriculum planner + validation

## FILES

`app/planning/validate.py`

- Unique IDs, `DE-\\d{3}`.
- Prerequisites exist, no cycles (Kahn or DFS).
- `source_files` subset of analysis important/inventory paths.
- `adapter` in allowed set; if adapter is executable but not in `detected_adapters`, coerce to `plan_only`.

`app/planning/generate.py`

- LLM with `planner.txt` + analysis JSON + optional notes.
- Validate; on failure, one retry with validator error string; then raise.

`app/planning/manual.py`

- Accept a mentor-supplied `LearningPlan`, validate, store as draft.

## TESTS `tests/test_planner.py`

- Valid linear plan passes.
- Cycle rejected.
- Unknown file rejected.
- Duplicate IDs rejected.
- Mocked LLM generate returns coerced `plan_only` when adapter is `pyspark` but detection is only `python_pytest`.

## VERIFY

```bash
PYTHONPATH=/home/ranga/opencode/tutor/backend /home/ranga/opencode/tutor/.venv/bin/python -m pytest /home/ranga/opencode/tutor/tests/test_planner.py -q
```

---

# TASK 07 — Assignment compiler + leak check

## FILES

`app/assignments/leakcheck.py`

- `assert_no_leak(artifact: AssignmentArtifact, reference_files: list[FileBlob])`
- Fail if any reference function body longer than 40 non-comment lines appears as a subsequence in starter/hints/task.
- Fail if `hidden_tests` paths appear in starter_files.
- Fail if starter has no `TODO`.

`app/assignments/compile.py`

- For one plan item, send compiler prompt + source excerpts + reference copy of those files.
- Validate `AssignmentArtifact`.
- Run leakcheck.
- Starter files must parse as Python if they end in `.py` (`ast.parse`).

Do not run tests yet (no sandbox until TASK 10). Store artifact JSON on the assignment row unpublished.

## TESTS `tests/test_assignment_compiler.py`

- Mock LLM returns artifact without TODO → rejected.
- Mock LLM returns artifact that copies reference body → rejected.
- Happy-path mock with TODO + NotImplementedError accepted.

## VERIFY

```bash
PYTHONPATH=/home/ranga/opencode/tutor/backend /home/ranga/opencode/tutor/.venv/bin/python -m pytest /home/ranga/opencode/tutor/tests/test_assignment_compiler.py -q
```

---

# TASK 08 — Fixtures + learner workspace

## FILES

Replace/expand `fixtures/python_etl/` as a tiny real project:

```
fixtures/python_etl/
  README.md
  requirements.txt          # pandas pytest
  src/orders/__init__.py
  src/orders/normalize.py   # complete reference: copy, parse dates to UTC, drop bad ids, reorder columns
  tests/test_normalize.py   # public tests
```

`normalize.py` reference must be complete and correct. Include `ORDER_SCHEMA = ["order_id", "ts_utc", "amount"]`.

`fixtures/duckdb_pipeline/`:

```
README.md
sql/orders.sql              # CREATE TABLE + INSERT sample
sql/normalize.sql           # complete SELECT producing canonical rows
```

`app/assignments/workspace.py`

- Copy snapshot to `data/projects/<id>/learner/<ws>/`.
- Overlay `starter_files`.
- Write public tests into workspace.
- Write reference copy under `reference/<assignment-id>/` (not inside learner dir).
- Write hidden tests under `data/projects/<id>/hidden/<assignment-id>/` (not inside learner dir).

Learner listing API later must not serve `reference/` or `hidden/`.

## TESTS `tests/test_workspace.py`

- After materialize, learner dir contains starter `NotImplementedError`.
- Learner dir does not contain hidden tests or the full reference transform.
- Reference dir does contain the original implementation.

## VERIFY

```bash
PYTHONPATH=/home/ranga/opencode/tutor/backend /home/ranga/opencode/tutor/.venv/bin/python -m pytest /home/ranga/opencode/tutor/tests/test_workspace.py -q
```

---

# TASK 09 — Adapter protocol + python_pytest + sql_duckdb

## FILES

`app/adapters/base.py`:

```python
from pathlib import Path
from typing import Protocol
from app.schemas import AssignmentArtifact, Evaluation

class ProjectAdapter(Protocol):
    name: str
    def detect(self, snapshot: Path) -> bool: ...
    def test_command(self, assignment: AssignmentArtifact) -> list[str]: ...
    def evaluate_in_container_args(self, assignment: AssignmentArtifact) -> list[str]: ...
```

Registry dict `ADAPTERS`.

`python_pytest.py`: `detect` if `tests/` or `pytest` in requirements. Command default `pytest -q`.

`sql_duckdb.py`: `detect` if `.sql` files exist and no `dbt_project.yml`. Evaluation command: run DuckDB CLI or `python -c` with `duckdb` if added to sandbox later. For MVP, evaluation of SQL adapter may execute `duckdb :memory: .read file.sql` inside the sandbox image once duckdb is installed in TASK 10. If duckdb is not in the image yet, `detect` can still return true but `evaluate` raises `NotImplementedError` until TASK 10 — tests for SQL eval wait for TASK 10.

`tests/test_adapters.py`: detect true/false on the two fixtures.

## VERIFY

```bash
PYTHONPATH=/home/ranga/opencode/tutor/backend /home/ranga/opencode/tutor/.venv/bin/python -m pytest /home/ranga/opencode/tutor/tests/test_adapters.py -q
```

---

# TASK 10 — Sandbox image + evaluator

## FILES

`sandbox/Dockerfile`:

```dockerfile
FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    git ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir pytest pandas duckdb
RUN useradd -m -u 1000 -s /bin/bash student
WORKDIR /work
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod 755 /usr/local/bin/entrypoint.sh
USER student
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
```

`sandbox/entrypoint.sh`:

```bash
#!/bin/bash
set -euo pipefail
TIMEOUT="${TIMEOUT:-25}"
if [ "$#" -eq 0 ]; then
  echo "usage: entrypoint.sh <cmd> [args...]" >&2
  exit 2
fi
exec timeout --signal=KILL "${TIMEOUT}s" "$@"
```

`app/eval/sandbox.py`: `run(command, mounts, timeout)` using docker py client with security flags from the security model.

`app/eval/evaluate.py`:

- Mount learner workspace at `/work` read-write via tmpfs copy: copy workspace into a temp dir, mount that.
- Mount hidden tests at `/hidden:ro` if present.
- Run adapter command.
- Parse pytest output for passed/failed; for SQL, look for a printed `ALL_TESTS_PASSED` token from a wrapper.
- Fill `Evaluation`. Never call the LLM.

## TESTS

`tests/test_evaluator.py`: workspace from python_etl starter fails public tests; after copying reference into temp workspace, tests pass.

`tests/test_sandbox_security.py`: container run with `curl` or `python -c "import socket; socket.socket().connect(('1.1.1.1',53))"` fails (network disabled). Command should error, not succeed.

## COMMANDS

```bash
chmod +x /home/ranga/opencode/tutor/sandbox/entrypoint.sh
docker build -t de-tutor-sandbox:latest /home/ranga/opencode/tutor/sandbox
PYTHONPATH=/home/ranga/opencode/tutor/backend /home/ranga/opencode/tutor/.venv/bin/python -m pytest /home/ranga/opencode/tutor/tests/test_evaluator.py /home/ranga/opencode/tutor/tests/test_sandbox_security.py -q
```

## VERIFY

Image exists. Evaluator tests passed. Network test does not reach the internet.

---

# TASK 11 — Socratic tutor

## FILES

`app/tutor/prompt.py` loads `tutor.txt`.

`app/tutor/chat.py` `handle_chat(assignment_id, req) -> ChatResponse`

- System prompt + assignment learner-visible fields (no hidden tests, no reference).
- If `req.code` or submission present, run evaluator first and attach Evaluation JSON.
- OpenRouter complete **without** JSON mode, temperature 0.3.
- `ChatResponse(reply, passed, evaluation)`.
- `passed` comes only from Evaluation, not from the model text.

Leak test: mock LLM; also a checker that if model output contains a 60-char substring from reference `normalize.py` body, replace reply with `"I cannot provide the full solution. Try the next failing test."` and set a flag. Implement `app/assignments/leakcheck.py` function `strip_reference_leak(text, references)`.

## TESTS `tests/test_tutor.py`

- Mock eval passed=false, mock LLM returns reference snippet → stripped.
- `passed` in response matches evaluation, not LLM wording.

## VERIFY

```bash
PYTHONPATH=/home/ranga/opencode/tutor/backend /home/ranga/opencode/tutor/.venv/bin/python -m pytest /home/ranga/opencode/tutor/tests/test_tutor.py -q
```

---

# TASK 12 — HTTP API

## FILES

Routers under `app/api/` as listed. Mount in `main.py`. Static `web/` at `/` if the directory exists.

Behavior:

- Ingest endpoints call ingest, return `{id, snapshot_hash}`.
- Analyze/plan/assignment generate/evaluate return `{job_id}` and run `BackgroundTasks`.
- `GET /api/jobs/{id}` returns status and result.
- `GET /api/assignments/{id}` for learner role query `?view=learner` omits hidden_tests and any reference.
- Mentor default view includes everything.
- For MVP, no auth: `view=learner` vs `view=mentor` query param is enough. Default `mentor` on plan/assignment PATCH, default `learner` on chat.

`tests/test_plan_api.py` and `tests/test_api_workflow.py`:

1. Health.
2. Local ingest fixture.
3. Mock LLM analyze + plan generate + compile.
4. Approve plan.
5. Materialize workspace.
6. GET assignment `view=learner` has no `hidden_tests`.

Use `fastapi.testclient.TestClient`. Mock jobs to run synchronously in tests by calling the function inline.

## VERIFY

```bash
PYTHONPATH=/home/ranga/opencode/tutor/backend /home/ranga/opencode/tutor/.venv/bin/python -m pytest /home/ranga/opencode/tutor/tests/test_plan_api.py /home/ranga/opencode/tutor/tests/test_api_workflow.py -q
```

---

# TASK 13 — Static mentor/learner UI + run

## FILES

`web/styles.css`: readable sans-serif, max width 960px, monospace for code.

`web/index.html`: links to mentor and learner.

`web/mentor.html` + `app.js` mentor mode:

- Form: local path, git URL, zip file.
- Buttons: Analyze, Generate plan, Approve, Generate assignments, Publish.
- Editable textarea of plan JSON.
- Preview of assignment JSON.

`web/learner.html`:

- Load assignment id from `?id=`.
- Show spec, inspect file list, starter in textarea, message box, Submit, Hints.
- Show evaluation passed/fail and tutor reply.

Do not call OpenRouter from the browser.

## COMMANDS

```bash
cp -n /home/ranga/opencode/tutor/.env.example /home/ranga/opencode/tutor/.env
cd /home/ranga/opencode/tutor/backend
PYTHONPATH=/home/ranga/opencode/tutor/backend \
  /home/ranga/opencode/tutor/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## VERIFY

```bash
curl -s http://127.0.0.1:8000/api/health
test -f /home/ranga/opencode/tutor/web/mentor.html
test -f /home/ranga/opencode/tutor/web/learner.html
```

Health JSON `{"ok": true}`. Browser: `http://127.0.0.1:8000/`.

---

# TASK 14 — E2E fixtures + optional adapters (stop before this for MVP)

Do not start until the operator says so.

1. `tests/e2e/test_python_etl.py`: ingest fixture, mock planner to one assignment wrapping `normalize.py`, compile with mock artifact matching partial-algorithm style, workspace, evaluator fail then pass after copying reference.
2. `tests/e2e/test_duckdb_pipeline.py`: same for SQL if duckdb eval works.
3. Stub `adapters/dbt.py` and `adapters/pyspark.py` with `detect()` only; `evaluate` raises `PlanOnly`.
4. Analyzer may label dbt/pyspark in `stack` without offering executable grading.

## VERIFY

```bash
PYTHONPATH=/home/ranga/opencode/tutor/backend /home/ranga/opencode/tutor/.venv/bin/python -m pytest /home/ranga/opencode/tutor/tests/e2e -q
```

---

## Operator checklist

| Order | Prompt to small model | Done when |
|---|---|---|
| 1 | Do ONLY TASK 00 | prompts + security doc + dirs |
| 2 | Do ONLY TASK 01 | `test_schemas.py` passed |
| 3 | Do ONLY TASK 02 | alembic upgrade + storage test |
| 4 | Do ONLY TASK 03 | ingestion tests including ZIP traversal |
| 5 | Do ONLY TASK 04 | deterministic analyzer tests |
| 6 | Do ONLY TASK 05 | mocked LLM analysis + health |
| 7 | Do ONLY TASK 06 | planner validation tests |
| 8 | Do ONLY TASK 07 | compiler leakcheck tests |
| 9 | Do ONLY TASK 08 | workspace does not leak reference |
| 10 | Do ONLY TASK 09 | adapter detect tests |
| 11 | Do ONLY TASK 10 | docker image + evaluator + no network |
| 12 | Do ONLY TASK 11 | tutor leak strip tests |
| 13 | Do ONLY TASK 12 | API workflow tests |
| 14 | Do ONLY TASK 13 | `/api/health` and static pages |
| 15 | Do ONLY TASK 14 | e2e (optional) |

Stop after TASK 13 for a usable MVP.

MVP includes: all three ingest methods, analysis, AI + manual plans, partial-algorithm assignments, Python/pytest grading, DuckDB adapter detect (eval if TASK 10 installed duckdb), mentor/learner HTML, Socratic tutor, progress rows.

dbt/PySpark executable grading is TASK 14+.

---

## Mentor vs learner visibility

| Asset | Mentor | Learner | LLM tutor |
|---|---|---|---|
| Snapshot source | yes | via workspace overlay only | excerpts, no secrets |
| Analysis JSON | yes | no | yes |
| Plan JSON | yes | titles of unlocked items only | current item only |
| Reference implementation | yes | no | no |
| Hidden tests | yes | no | no |
| Starter + public tests | yes | yes | yes |
| Evaluation JSON | yes | yes | yes |
| Git credentials | never | never | never |
