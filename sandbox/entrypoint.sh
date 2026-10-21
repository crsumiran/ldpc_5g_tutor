#!/bin/bash
set -euo pipefail
TIMEOUT="${TIMEOUT:-25}"
if [ "$#" -eq 0 ]; then
  echo "usage: entrypoint.sh <cmd> [args...]" >&2
  exit 2
fi
exec timeout --signal=KILL "${TIMEOUT}s" "$@"
