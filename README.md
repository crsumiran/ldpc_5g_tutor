# LDPC 5G Hardware Accelerator Tutor

A local, browser-based tutor for learning LDPC decoding and hardware design through short theory chapters, Python assignments, public tests, and an optional AI guide. The interface is a notebook-style web app; it does not require Jupyter.

The LDPC course is at `/?course=ldpc-5g` and `/labs/ldpc-5g`. The same app also includes the Verilog cache course (`/?course=cache-lab`) and optical-flow course (`/?course=optical-flow`). The LDPC material is an educational foundation, not a complete 5G NR decoder or a finished hardware accelerator.

The independent `notebook_tutor/` directory contains a standalone notebook assignment and a separate implementation plan; it is not started by the main Compose launcher.

## Launch on Linux or WSL

Requirements: Docker Engine with Docker Compose v2, and permission to use the Docker socket (`/var/run/docker.sock`). The API starts isolated runner containers through that socket. Ports 3000 and 8000 must be available.

Clone the repository and launch it:

```bash
git clone https://github.com/crsumiran/ldpc_5g_tutor.git
cd ldpc_5g_tutor
bash scripts/launch.sh
```

Open <http://localhost:3000/?course=ldpc-5g>. The API health endpoint is <http://localhost:8000/api/health>.

The launch script creates `.env` from `.env.example` when needed, sets `PROJECT_ROOT` to this checkout's absolute path for Compose, then builds and starts the services. You can run it again after pulling changes. To stop the services, run `docker compose down` from the checkout. Learner work stored under `data/` remains on disk.

AI guide calls are optional. The app can use the configured OpenCode/OpenRouter setup, or you can enter your own OpenRouter key and choose a model in the page's AI settings. Do not commit `.env` or put a key in a source file.

## Learner data and portability

The public repository contains the full course source, including the cache reference RTL and testbenches marked hidden in the app. Those files are therefore public and must not be treated as confidential grading material. Runtime learner state is created locally in `data/` (SQLite database, workspaces, and run reports) and is excluded from Git. To move progress to another machine, stop the app and transfer the relevant `data/` directory separately; the browser's saved session ID may also need to be restored. Never copy `.env` as a way to transfer credentials. See [RECOVERY_PROMPT.md](RECOVERY_PROMPT.md) for a cross-machine handoff.

## Development and verification

The application is split into a FastAPI backend (`backend/`), Next.js frontend (`web/`), course content (`curriculum/`), isolated execution images (`sandbox/` and `harness/`), and regression tests (`tests/`).

```bash
docker compose up -d --build
PYTHONPATH=backend .venv/bin/python -m pytest tests/ -q
```

The Python test command assumes a local virtual environment with `backend/requirements.txt` installed. Frontend checks are in `web/package.json` (`npm ci`, then lint/typecheck/build scripts). Some live sandbox checks require Docker and are opt-in. See [HANDOFF.md](HANDOFF.md), [docs/LDPC_GUIDE.md](docs/LDPC_GUIDE.md), and [docs/security-model.md](docs/security-model.md).

## Important deployment boundary

This is a local learning tool. The API has no user authentication and receives host Docker-socket access so it can create constrained test containers. Keep it on a trusted machine/network; do not expose its ports publicly without adding an authentication and deployment security layer.
