# Cross-Machine Recovery Prompt

Use this prompt with a coding agent after cloning this repository on another Linux machine or in WSL. It describes the current multi-course tutor, not the older cache-only version.

```text
You are taking over the LDPC 5G Hardware Accelerator Tutor repository. First read README.md, HANDOFF.md, the newest entries in EXPERIMENT_LOG.md, docker-compose.yml, docs/LDPC_GUIDE.md, and docs/security-model.md. Preserve all existing learner work and credentials. Never print or commit secrets, learner databases/workspaces, private reference implementations, or hidden tests.

Purpose and current course routes:
- LDPC theory and 18 Python checkpoints: /?course=ldpc-5g
- Verilog direct-mapped cache course: /?course=cache-lab
- Optical-flow Python course: /?course=optical-flow
- The LDPC course is a foundational educational project, not a complete NR decoder or finished accelerator.

Host requirements:
- Linux or WSL with Docker Engine and Docker Compose v2.
- The host user can run Docker and access /var/run/docker.sock.
- Ports 3000 and 8000 are available.
- Keep this checkout at a stable absolute path. Compose sets PROJECT_ROOT to that path because nested runner containers need identical host and API-container bind-mount paths.

Launch a fresh checkout:
1. Run `bash scripts/launch.sh` at the repository root. It copies .env.example to .env only if .env is absent, sets PROJECT_ROOT for this checkout, and runs `docker compose up -d --build`.
2. Check `docker compose ps` and `curl -fsS http://127.0.0.1:8000/api/health`.
3. Open `http://127.0.0.1:3000/?course=ldpc-5g`.
4. Open `http://127.0.0.1:3000/?course=cache-lab` for the Verilog course or `http://127.0.0.1:3000/?course=optical-flow` for the optical-flow course.

The app can run without a model key using its authored/local fallback behavior. For AI answers, set up a current OpenRouter key through the UI or a local .env. Never copy an old .env, paste a secret into logs, or commit one. Model routes and provider limits can change.

Learner data:
- Runtime state is under `data/`, which is intentionally ignored by Git.
- A source-only clone starts with fresh local progress.
- To restore progress, stop the app and copy the matching database and `data/labs/<session-id>/` workspace from a trusted backup. Keep the directory structure and set PROJECT_ROOT to the new checkout path. Do not overwrite a newer database/workspace without making a backup.
- Browser local storage also stores the active course session ID. If the browser profile changes, restore the correct course's session ID from the old browser or select the session through the app if available.
- `.env` is machine-specific and is not part of a progress backup. Recreate it from `.env.example` and set a new key if needed.

Troubleshooting:
- If Compose reports an invalid project root, run the launch script from the checkout again.
- If page/API ports are occupied, identify the process before changing the port mappings.
- If nested test containers fail to start, check Docker socket permissions and `docker compose ps`.
- If a route is stale after source changes, rebuild with `bash scripts/launch.sh`.
- Never delete `data/` to troubleshoot. Inspect logs first with `docker compose logs --tail=200 api web opencode`.

Before changing curricula or runner behavior, inspect the relevant course manifest, public tests, runner, and existing tests. Run regressions with disposable DATA_DIR/database settings so learner progress remains untouched. Do not claim a live model test unless one was actually run.

When handing off, report the checkout path, platform, Docker/Compose availability, health endpoints, test results, whether progress was restored or fresh, and the next concrete step.
```

## Moving the tutor between machines

The repository is source-only. Copy `data/` separately only when learner progress must move, and create a fresh `.env` on the destination. The repository's [README](README.md) has the normal first-launch steps.
