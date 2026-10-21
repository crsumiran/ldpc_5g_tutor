# Verilog Tutor — Small-Model Implementation Plan

Feed the implementing model **one TASK at a time**. Do not let it choose frameworks, invent APIs, or skip verification.

Source: `opensource_tutor_strategy.md`

---

## Locked decisions (do not reopen)

| Decision | Choice | Why |
|---|---|---|
| Framework | Plain Python + FastAPI. **Not** AutoGen. **Not** OpenHands. | Smaller model can write this. Two-agent pattern is just two functions. |
| Brain | OpenRouter via `OPENROUTER_API_KEY`. Model from env `TUTOR_MODEL` default `openai/gpt-4o-mini`. | Swap later. Hermes/Ollama is TASK 10 only. |
| Executor (Agent A) | Python + Docker. Not an LLM. | Code exec does not need a model. |
| Tutor (Agent B) | One LLM call with tools. System prompt is frozen below. | Matches the strategy doc. |
| Sandbox | Docker, no network, memory/CPU/time limits. | Public-deploy safety. |
| Frontend | Static HTML in `frontend/`. **Not** Next.js yet. | Defer React to TASK 11. |
| Curriculum | One lesson only for MVP: `and2`. | Unblocks the loop. |
| Python | 3.11+ | |
| Workdir | `/home/ranga/opencode/tutor` | Never write outside this tree except Docker image build. |

If a step is already done, skip it. Check the **VERIFY** block first.

---

## Frozen tutor system prompt

Write this **exactly** to `backend/prompts/tutor.txt` in TASK 04. Do not paraphrase.

```
You are an expert FPGA Engineer and a Socratic Verilog tutor. Your goal is to help the student learn without giving them the final answers.

# Rules of Engagement
1. **No Direct Solutions:** Never write the correct code for the student. If they ask for the answer, politely decline and provide a conceptual hint instead.
2. **Utilize the Executor:** When the student submits an assignment, you must hand the code over to the executor tool. Wait for its terminal output report.
3. **Analyze and Hint:** Review the compiler errors or simulation mismatch from the Executor. Formulate your response based on this data. For example: "The compiler found a syntax error on line 14. Remember the difference between blocking (=) and non-blocking (<=) assignments in sequential logic."
4. **Curriculum:** Follow the predefined curriculum. Do not move to the next topic until the student's code successfully compiles and passes the testbench.

# Tone
Encouraging, strictly pedagogical, and technical.

# Tools
You have one tool: run_verilog. Use it whenever the student submits Verilog.
```

---

## Target tree (create only these paths)

```
/home/ranga/opencode/tutor/
  IMPLEMENTATION_PLAN.md          (this file — do not modify)
  opensource_tutor_strategy.md
  .env.example
  .gitignore
  docker-compose.yml
  sandbox/
    Dockerfile
    entrypoint.sh
  curriculum/
    lessons.json
    and2/
      spec.md
      tb_and2.v
      golden_and2.v               (never served to the student or the tutor LLM)
  backend/
    requirements.txt
    app/
      __init__.py
      main.py
      config.py
      models.py
      tutor.py
      llm.py
      executor.py
    prompts/
      tutor.txt
  frontend/
    index.html
    app.js
    styles.css
  tests/
    test_executor.py
    test_api.py
    fixtures/
      good_and2.v
      bad_and2.v
```

---

## How a small model must work

1. Read only the TASK you were given.
2. Run every COMMAND in order.
3. Write files exactly as specified. Do not add comments, extras, or refactors.
4. Run VERIFY. If it fails, fix only that TASK. Do not start the next TASK.
5. Stop. Reply with: `TASK NN DONE` or `TASK NN FAILED: <one line>`.

Operator prompt template:

```
Read /home/ranga/opencode/tutor/IMPLEMENTATION_PLAN.md
Do ONLY TASK 0N. Do not start any other task.
```

---

# TASK 00 — Prerequisites

## COMMANDS

```bash
python3 --version
docker --version
docker info >/dev/null
test -n "$OPENROUTER_API_KEY" && echo KEY_SET || echo KEY_MISSING
mkdir -p /home/ranga/opencode/tutor/{sandbox,curriculum/and2,backend/app,backend/prompts,frontend,tests/fixtures}
```

`python3` must be 3.11+. `docker info` must succeed. `KEY_MISSING` is OK until TASK 08.

## FILES

Create `/home/ranga/opencode/tutor/.gitignore`:

```
.env
__pycache__/
*.pyc
.venv/
node_modules/
*.vcd
```

Create `/home/ranga/opencode/tutor/.env.example`:

```
OPENROUTER_API_KEY=
TUTOR_MODEL=openai/gpt-4o-mini
SANDBOX_IMAGE=verilog-tutor-sandbox:latest
SANDBOX_TIMEOUT_SEC=10
SANDBOX_MEM=256m
API_HOST=0.0.0.0
API_PORT=8000
```

## VERIFY

```bash
test -f /home/ranga/opencode/tutor/.gitignore
test -f /home/ranga/opencode/tutor/.env.example
test -d /home/ranga/opencode/tutor/backend/app
```

---

# TASK 01 — Sandbox image

## FILES

Create `/home/ranga/opencode/tutor/sandbox/Dockerfile`:

```dockerfile
FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    iverilog verilator ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN useradd -m -u 1000 -s /bin/bash student
WORKDIR /work
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod 755 /usr/local/bin/entrypoint.sh
USER student
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
```

Create `/home/ranga/opencode/tutor/sandbox/entrypoint.sh`:

```bash
#!/bin/bash
set -euo pipefail
TIMEOUT="${TIMEOUT:-8}"
if [ "$#" -eq 0 ]; then
  echo "usage: entrypoint.sh <cmd> [args...]" >&2
  exit 2
fi
exec timeout --signal=KILL "${TIMEOUT}s" "$@"
```

## COMMANDS

```bash
chmod +x /home/ranga/opencode/tutor/sandbox/entrypoint.sh
docker build -t verilog-tutor-sandbox:latest /home/ranga/opencode/tutor/sandbox
```

## VERIFY

```bash
docker run --rm --network none --memory 256m --cpus 0.5 \
  --read-only --tmpfs /tmp:rw,size=16m \
  -v /home/ranga/opencode/tutor/curriculum/and2:/work:ro \
  verilog-tutor-sandbox:latest iverilog -V | head -n 1
```

Expect a line containing `Icarus Verilog`. Image must exist: `docker image inspect verilog-tutor-sandbox:latest`.

---

# TASK 02 — Curriculum (and2 only)

## FILES

Create `/home/ranga/opencode/tutor/curriculum/lessons.json`:

```json
{
  "lessons": [
    {
      "id": "and2",
      "title": "2-input AND gate",
      "module": "and2",
      "student_file": "and2.v",
      "testbench": "tb_and2.v",
      "pass_token": "ALL_TESTS_PASSED"
    }
  ]
}
```

Create `/home/ranga/opencode/tutor/curriculum/and2/spec.md`:

```markdown
# Lesson and2

Write a Verilog module named `and2` with:
- inputs: `a`, `b`
- output: `y`
- function: `y = a AND b`

Do not write a testbench. The tutor provides one.
```

Create `/home/ranga/opencode/tutor/curriculum/and2/tb_and2.v`:

```verilog
`timescale 1ns/1ps
module tb_and2;
  reg a, b;
  wire y;
  and2 dut(.a(a), .b(b), .y(y));
  integer errors;
  initial begin
    errors = 0;
    a = 0; b = 0; #1; if (y !== 1'b0) errors = errors + 1;
    a = 0; b = 1; #1; if (y !== 1'b0) errors = errors + 1;
    a = 1; b = 0; #1; if (y !== 1'b0) errors = errors + 1;
    a = 1; b = 1; #1; if (y !== 1'b1) errors = errors + 1;
    if (errors == 0) $display("ALL_TESTS_PASSED");
    else $display("TESTS_FAILED %0d", errors);
    $finish;
  end
endmodule
```

Create `/home/ranga/opencode/tutor/curriculum/and2/golden_and2.v`:

```verilog
module and2(input a, input b, output y);
  assign y = a & b;
endmodule
```

Create `/home/ranga/opencode/tutor/tests/fixtures/good_and2.v` — same contents as `golden_and2.v`.

Create `/home/ranga/opencode/tutor/tests/fixtures/bad_and2.v`:

```verilog
module and2(input a, input b, output y);
  assign y = a | b;
endmodule
```

## COMMANDS

```bash
docker run --rm --network none --memory 256m --cpus 0.5 \
  -v /home/ranga/opencode/tutor/curriculum/and2:/work:ro \
  -v /home/ranga/opencode/tutor/tests/fixtures/good_and2.v:/tmp/and2.v:ro \
  --tmpfs /tmp/run:rw,size=16m \
  -w /tmp/run \
  verilog-tutor-sandbox:latest \
  iverilog -o sim /tmp/and2.v /work/tb_and2.v
```

That compile may fail because `/tmp/run` is the workdir and iverilog writes `sim` there — the tmpfs is fine. Then:

```bash
docker run --rm --network none --memory 256m --cpus 0.5 \
  -v /home/ranga/opencode/tutor/curriculum/and2:/lesson:ro \
  -v /home/ranga/opencode/tutor/tests/fixtures/good_and2.v:/lesson_in/and2.v:ro \
  --tmpfs /work:rw,size=16m \
  -w /work \
  verilog-tutor-sandbox:latest \
  bash -c 'cp /lesson_in/and2.v /lesson/tb_and2.v /work/ && iverilog -o sim and2.v tb_and2.v && vvp sim'
```

## VERIFY

Good fixture output must contain `ALL_TESTS_PASSED`.

Repeat the last `docker run` with `bad_and2.v` instead of `good_and2.v`. Output must contain `TESTS_FAILED`.

---

# TASK 03 — Python package + executor

## FILES

Create `/home/ranga/opencode/tutor/backend/requirements.txt`:

```
fastapi==0.115.6
uvicorn==0.34.0
httpx==0.28.1
pydantic==2.10.4
pydantic-settings==2.7.1
docker==7.1.0
pytest==8.3.4
```

Create `/home/ranga/opencode/tutor/backend/app/__init__.py` — empty file.

Create `/home/ranga/opencode/tutor/backend/app/config.py`:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openrouter_api_key: str = ""
    tutor_model: str = "openai/gpt-4o-mini"
    sandbox_image: str = "verilog-tutor-sandbox:latest"
    sandbox_timeout_sec: int = 10
    sandbox_mem: str = "256m"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    curriculum_dir: str = "/home/ranga/opencode/tutor/curriculum"


settings = Settings()
```

Create `/home/ranga/opencode/tutor/backend/app/models.py`:

```python
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    lesson_id: str = "and2"
    message: str
    code: str | None = None
    history: list[dict] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply: str
    passed: bool = False
    executor_output: str | None = None


class ExecResult(BaseModel):
    compile_ok: bool
    passed: bool
    stdout: str
    stderr: str
    exit_code: int
```

Create `/home/ranga/opencode/tutor/backend/app/executor.py`:

```python
import tempfile
from pathlib import Path

import docker
from docker.errors import ContainerError, ImageNotFound

from app.config import settings
from app.models import ExecResult

_SHELL = """
set -e
cp /in/student.v /work/and2.v
cp /lesson/tb_and2.v /work/tb_and2.v
cd /work
iverilog -o sim and2.v tb_and2.v
vvp sim
"""


def run_verilog(lesson_id: str, student_src: str) -> ExecResult:
    lesson = Path(settings.curriculum_dir) / lesson_id
    tb = lesson / f"tb_{lesson_id}.v"
    if not tb.is_file():
        return ExecResult(
            compile_ok=False,
            passed=False,
            stdout="",
            stderr=f"unknown lesson: {lesson_id}",
            exit_code=2,
        )

    client = docker.from_env()
    with tempfile.TemporaryDirectory(prefix="vt-") as tmp:
        student_path = Path(tmp) / "student.v"
        student_path.write_text(student_src, encoding="utf-8")
        try:
            out = client.containers.run(
                settings.sandbox_image,
                command=["bash", "-lc", _SHELL],
                network_disabled=True,
                mem_limit=settings.sandbox_mem,
                nano_cpus=500_000_000,
                read_only=True,
                cap_drop=["ALL"],
                security_opt=["no-new-privileges:true"],
                tmpfs={"/work": "rw,size=16m,uid=1000", "/tmp": "rw,size=8m,uid=1000"},
                volumes={
                    str(student_path.parent): {"bind": "/in", "mode": "ro"},
                    str(lesson): {"bind": "/lesson", "mode": "ro"},
                },
                working_dir="/work",
                remove=True,
                stdout=True,
                stderr=True,
            )
            text = out.decode("utf-8", errors="replace") if isinstance(out, bytes) else str(out)
            passed = "ALL_TESTS_PASSED" in text
            return ExecResult(
                compile_ok=True,
                passed=passed,
                stdout=text,
                stderr="",
                exit_code=0,
            )
        except ImageNotFound:
            return ExecResult(
                compile_ok=False,
                passed=False,
                stdout="",
                stderr="sandbox image missing; run TASK 01",
                exit_code=127,
            )
        except ContainerError as exc:
            err = (exc.stderr or b"").decode("utf-8", errors="replace")
            compile_ok = "iverilog" not in err.lower() or "error" not in err.lower()
            if "syntax" in err.lower() or "error:" in err.lower():
                compile_ok = False
            return ExecResult(
                compile_ok=compile_ok,
                passed=False,
                stdout="",
                stderr=err or str(exc),
                exit_code=exc.exit_status or 1,
            )
```

Create `/home/ranga/opencode/tutor/tests/test_executor.py`:

```python
from pathlib import Path

from app.executor import run_verilog

FIXTURES = Path("/home/ranga/opencode/tutor/tests/fixtures")


def test_good_passes():
    src = (FIXTURES / "good_and2.v").read_text()
    r = run_verilog("and2", src)
    assert r.compile_ok
    assert r.passed
    assert "ALL_TESTS_PASSED" in r.stdout


def test_bad_fails_tests():
    src = (FIXTURES / "bad_and2.v").read_text()
    r = run_verilog("and2", src)
    assert r.compile_ok
    assert not r.passed
    assert "TESTS_FAILED" in r.stdout or "TESTS_FAILED" in r.stderr


def test_syntax_error():
    r = run_verilog("and2", "module oops endmodule")
    assert not r.passed
    assert r.exit_code != 0
```

## COMMANDS

```bash
python3 -m venv /home/ranga/opencode/tutor/.venv
/home/ranga/opencode/tutor/.venv/bin/pip install -r /home/ranga/opencode/tutor/backend/requirements.txt
cd /home/ranga/opencode/tutor/backend && /home/ranga/opencode/tutor/.venv/bin/python -m pytest /home/ranga/opencode/tutor/tests/test_executor.py -q
```

## VERIFY

`pytest` shows `3 passed`. If `test_bad_fails_tests` cannot see `TESTS_FAILED` because vvp output landed in stderr, update `executor.py` to always join stdout+stderr into both fields, then re-run pytest. Do not change the tests' assertions.

---

# TASK 04 — LLM client + tutor

## FILES

Write the frozen prompt from the top of this document to `/home/ranga/opencode/tutor/backend/prompts/tutor.txt`.

Create `/home/ranga/opencode/tutor/backend/app/llm.py`:

```python
import json
import httpx

from app.config import settings

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "run_verilog",
            "description": "Compile and simulate the student's Verilog against the lesson testbench.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lesson_id": {"type": "string"},
                    "code": {"type": "string"},
                },
                "required": ["lesson_id", "code"],
            },
        },
    }
]


def complete(messages: list[dict], tools: list[dict] | None = None) -> dict:
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.tutor_model,
        "messages": messages,
        "temperature": 0.3,
    }
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"
    with httpx.Client(timeout=60.0) as client:
        r = client.post(OPENROUTER_URL, headers=headers, json=payload)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]
```

Create `/home/ranga/opencode/tutor/backend/app/tutor.py`:

```python
from pathlib import Path

from app.executor import run_verilog
from app.llm import TOOLS, complete
from app.models import ChatRequest, ChatResponse

PROMPT_PATH = Path("/home/ranga/opencode/tutor/backend/prompts/tutor.txt")


def _system() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def handle_chat(req: ChatRequest) -> ChatResponse:
    messages: list[dict] = [{"role": "system", "content": _system()}]
    messages.extend(req.history)
    user = req.message
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
```

## VERIFY

```bash
test -s /home/ranga/opencode/tutor/backend/prompts/tutor.txt
grep -q "No Direct Solutions" /home/ranga/opencode/tutor/backend/prompts/tutor.txt
/home/ranga/opencode/tutor/.venv/bin/python -c "from app.tutor import handle_chat; print('ok')"
```

Run the import check with `PYTHONPATH=/home/ranga/opencode/tutor/backend`.

---

# TASK 05 — FastAPI app

## FILES

Create `/home/ranga/opencode/tutor/backend/app/main.py`:

```python
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.models import ChatRequest, ChatResponse
from app.tutor import handle_chat

app = FastAPI(title="Verilog Tutor")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

CURRICULUM = Path(settings.curriculum_dir)


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/lessons")
def lessons():
    return (CURRICULUM / "lessons.json").read_text(encoding="utf-8")


@app.get("/api/lessons/{lesson_id}")
def lesson(lesson_id: str):
    spec = CURRICULUM / lesson_id / "spec.md"
    if not spec.is_file():
        raise HTTPException(404, "unknown lesson")
    return {"id": lesson_id, "spec": spec.read_text(encoding="utf-8")}


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    return handle_chat(req)


FRONTEND = Path("/home/ranga/opencode/tutor/frontend")
if FRONTEND.is_dir():
    app.mount("/", StaticFiles(directory=str(FRONTEND), html=True), name="frontend")
```

Fix `/api/lessons` so it returns parsed JSON, not a string. Change the body to:

```python
import json
return json.loads((CURRICULUM / "lessons.json").read_text(encoding="utf-8"))
```

Create `/home/ranga/opencode/tutor/tests/test_api.py`:

```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_lessons():
    r = client.get("/api/lessons")
    assert r.status_code == 200
    assert r.json()["lessons"][0]["id"] == "and2"


def test_lesson_spec():
    r = client.get("/api/lessons/and2")
    assert r.status_code == 200
    assert "and2" in r.json()["spec"]
```

## COMMANDS

```bash
cd /home/ranga/opencode/tutor/backend && PYTHONPATH=/home/ranga/opencode/tutor/backend /home/ranga/opencode/tutor/.venv/bin/python -m pytest /home/ranga/opencode/tutor/tests/test_api.py /home/ranga/opencode/tutor/tests/test_executor.py -q
```

## VERIFY

All tests passed. `/api/lessons` returns an object with a `lessons` array.

---

# TASK 06 — Frontend (static)

## FILES

Create `/home/ranga/opencode/tutor/frontend/index.html`:

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Verilog Tutor</title>
  <link rel="stylesheet" href="/styles.css" />
</head>
<body>
  <h1>Verilog Tutor</h1>
  <pre id="spec"></pre>
  <textarea id="code" rows="16" cols="80">module and2(input a, input b, output y);
  // your code
endmodule</textarea>
  <textarea id="msg" rows="3" cols="80">Please check my and2.</textarea>
  <button id="send">Submit</button>
  <pre id="out"></pre>
  <script src="/app.js"></script>
</body>
</html>
```

Create `/home/ranga/opencode/tutor/frontend/styles.css`:

```css
body { font-family: sans-serif; max-width: 900px; margin: 2rem auto; }
textarea, pre { width: 100%; font-family: monospace; }
button { margin: 0.5rem 0; padding: 0.4rem 1rem; }
```

Create `/home/ranga/opencode/tutor/frontend/app.js`:

```javascript
const specEl = document.getElementById("spec");
const outEl = document.getElementById("out");
const history = [];

async function load() {
  const r = await fetch("/api/lessons/and2");
  const j = await r.json();
  specEl.textContent = j.spec;
}
load();

document.getElementById("send").onclick = async () => {
  const message = document.getElementById("msg").value;
  const code = document.getElementById("code").value;
  const r = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ lesson_id: "and2", message, code, history }),
  });
  const j = await r.json();
  history.push({ role: "user", content: message });
  history.push({ role: "assistant", content: j.reply });
  outEl.textContent =
    (j.passed ? "PASSED\n" : "NOT PASSED\n") +
    j.reply +
    (j.executor_output ? "\n\n--- executor ---\n" + j.executor_output : "");
};
```

## VERIFY

```bash
test -f /home/ranga/opencode/tutor/frontend/index.html
test -f /home/ranga/opencode/tutor/frontend/app.js
```

---

# TASK 07 — Run scripts + compose

## FILES

Create `/home/ranga/opencode/tutor/docker-compose.yml`:

```yaml
services:
  api:
    image: python:3.11-slim
    working_dir: /home/ranga/opencode/tutor/backend
    command: ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
    env_file: .env
    ports:
      - "8000:8000"
    volumes:
      - /home/ranga/opencode/tutor:/home/ranga/opencode/tutor
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      PYTHONPATH: /home/ranga/opencode/tutor/backend
```

Prefer local run over compose. Create nothing else.

## COMMANDS (local run)

```bash
cp -n /home/ranga/opencode/tutor/.env.example /home/ranga/opencode/tutor/.env
# operator must put OPENROUTER_API_KEY in .env
cd /home/ranga/opencode/tutor/backend
PYTHONPATH=/home/ranga/opencode/tutor/backend \
  /home/ranga/opencode/tutor/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## VERIFY

In another shell:

```bash
curl -s http://127.0.0.1:8000/api/health
curl -s http://127.0.0.1:8000/api/lessons
```

Both return JSON. Browser: `http://127.0.0.1:8000/`.

---

# TASK 08 — End-to-end chat (needs API key)

## COMMANDS

```bash
GOOD=$(cat /home/ranga/opencode/tutor/tests/fixtures/good_and2.v)
python3 - <<PY
import json, os, urllib.request
src = open("/home/ranga/opencode/tutor/tests/fixtures/good_and2.v").read()
body = json.dumps({
  "lesson_id": "and2",
  "message": "Please check my code.",
  "code": src,
  "history": [],
}).encode()
req = urllib.request.Request(
  "http://127.0.0.1:8000/api/chat",
  data=body,
  headers={"Content-Type": "application/json"},
)
print(urllib.request.urlopen(req).read().decode())
PY
```

## VERIFY

JSON has `"passed": true`. `reply` must not contain a full correct module if you instead submit `bad_and2.v`. Repeat the curl with `bad_and2.v`; `"passed": false` and the reply is a hint, not `assign y = a & b`.

---

# TASK 09 — Security hardening (only if 00–08 pass)

Do these edits only:

1. In `executor.py`, reject student source longer than 20000 bytes.
2. Reject if student source contains `` `include ``, `$readmem`, `$fopen`, `fork`, or `c_os`.
3. Keep `network_disabled=True`, `cap_drop=["ALL"]`, `read_only=True`.
4. Add a pytest that `run_verilog("and2", '`include "/etc/passwd"')` returns `passed=False` and does not start a container if you can detect it pre-flight.

VERIFY: existing 3 executor tests still pass, plus the new reject test.

---

# TASK 10 — Local Hermes (optional, later)

Do not start until the operator says so.

1. `curl -fsSL https://ollama.com/install.sh | sh` only if ollama is missing.
2. `ollama pull hermes3`.
3. In `llm.py`, if `TUTOR_MODEL` starts with `ollama/`, POST to `http://127.0.0.1:11434/v1/chat/completions` instead of OpenRouter. Strip the `ollama/` prefix for the model name.
4. VERIFY: `TUTOR_MODEL=ollama/hermes3` + dummy key still serves `/api/health`. Chat may be slow; do not change prompts.

---

# TASK 11 — Next.js frontend (optional, later)

Do not start until the operator says so.

```bash
cd /home/ranga/opencode/tutor
npx --yes create-next-app@14 web --typescript --eslint --app --src-dir --no-tailwind --import-alias "@/*" --use-npm
```

Then recreate the same three UI pieces: spec fetch, code box, chat POST to `http://127.0.0.1:8000/api/chat`. Keep the static `frontend/` working.

---

# TASK 12 — AutoGen wrapper (optional, later)

Do not start until the operator says so.

Only wrap existing functions. Do not replace `executor.py`.

- Agent A name: `VerilogExecutor`. It may only call `run_verilog`.
- Agent B name: `SocraticTutor`. System prompt = `backend/prompts/tutor.txt`.
- Pin `autogen-agentchat` version in requirements when you add it.
- FastAPI `/api/chat` stays the public API.

---

## Operator checklist

| Order | Prompt to small model | Done when |
|---|---|---|
| 1 | Do ONLY TASK 00 | dirs + gitignore exist |
| 2 | Do ONLY TASK 01 | docker image builds, `iverilog -V` works |
| 3 | Do ONLY TASK 02 | good fixture prints `ALL_TESTS_PASSED` |
| 4 | Do ONLY TASK 03 | `pytest tests/test_executor.py` → 3 passed |
| 5 | Do ONLY TASK 04 | prompt file exact, import ok |
| 6 | Do ONLY TASK 05 | api+executor pytest all pass |
| 7 | Do ONLY TASK 06 | three frontend files exist |
| 8 | Do ONLY TASK 07 | `/api/health` returns `{"ok":true}` |
| 9 | Do ONLY TASK 08 | good code `passed: true` |
| 10 | Do ONLY TASK 09 | include-reject test passes |

Stop after TASK 08 for a usable MVP.
