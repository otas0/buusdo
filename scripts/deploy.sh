#!/usr/bin/env bash
# pyside6-deploy packaging skeleton for Windows / Linux / macOS artifacts.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if ! command -v pyside6-deploy >/dev/null 2>&1; then
  echo "Install UI extra first: pip install -e '.[ui]'" >&2
  echo "Then ensure pyside6-deploy is on PATH." >&2
  exit 1
fi

ENTRY="${ROOT}/buusdo/app.py"
OUT="${ROOT}/dist"
mkdir -p "${OUT}"

# Nuitka-backed deploy; outputs vary by host (.exe / .bin / .app).
pyside6-deploy "${ENTRY}" -f -c "${ROOT}/scripts/pyside6-deploy.spec.json" || {
  echo "pyside6-deploy failed; falling back to module reminder." >&2
  echo "Manual: pyside6-deploy buusdo/app.py" >&2
  exit 1
}

echo "Artifacts under ${OUT} (host-dependent)."
