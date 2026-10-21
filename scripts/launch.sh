#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required. Install Docker Engine and Compose v2, then retry." >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "Docker Compose v2 is required (docker compose)." >&2
  exit 1
fi

if [[ ! -f "$repo_root/.env" ]]; then
  cp "$repo_root/.env.example" "$repo_root/.env"
  echo "Created .env from .env.example. Add a local guide key only if you want one."
fi

if ! docker info >/dev/null 2>&1; then
  echo "Docker is not reachable. Start Docker and check access to its socket." >&2
  exit 1
fi

cd "$repo_root"
PROJECT_ROOT="$repo_root" docker compose up -d --build

echo "Tutor is starting. Open: http://localhost:3000/?course=ldpc-5g"
echo "API health: http://localhost:8000/api/health"
