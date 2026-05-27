#!/usr/bin/env bash
# Start the FastAPI backend (Git Bash / WSL / macOS / Linux).
set -e
cd "$(dirname "$0")/../backend"
export PATH="$HOME/.local/bin:$PATH"
PY=".venv/Scripts/python.exe"
[ -f "$PY" ] || PY=".venv/bin/python"   # non-Windows venv layout
"$PY" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
