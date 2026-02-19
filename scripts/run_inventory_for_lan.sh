#!/usr/bin/env bash
# Run the inventory app on the host so it's reachable from LAN (http://<Mac-IP>:5050).
# Docker Desktop on Mac often only allows localhost to published ports; running on the host avoids that.
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
# Prefer repo venv so Flask and deps are available (create with: python3 -m venv .venv && .venv/bin/pip install -r inventory/app/requirements.txt)
if [[ -x "$ROOT/.venv/bin/python" ]]; then
  PY="$ROOT/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
  PY=python3
elif command -v python >/dev/null 2>&1; then
  PY=python
else
  echo "Error: python or python3 not found" >&2
  exit 1
fi
echo "Starting inventory app for LAN access at http://0.0.0.0:5050"
echo "On this Mac: http://127.0.0.1:5050  —  From other devices: http://<this-machine-IP>:5050"
exec "$PY" inventory/app/app.py
