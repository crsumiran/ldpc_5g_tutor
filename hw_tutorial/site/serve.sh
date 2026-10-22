#!/usr/bin/env bash
# Rebuild the one-page tutorial from the chapter markdown and serve it locally.
#   ./serve.sh            -> http://localhost:8080
#   PORT=9000 ./serve.sh  -> http://localhost:9000
set -euo pipefail
cd "$(dirname "$0")"
PORT="${PORT:-8080}"
python3 build_page.py .. index.html --standalone
echo "Serving the hardware tutorial at http://localhost:${PORT}  (Ctrl+C to stop)"
exec python3 -m http.server "$PORT" --bind 127.0.0.1
