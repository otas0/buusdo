#!/usr/bin/env bash
# LaunchAgent wrapper: append stdout/stderr so kickstart/hourly runs do not truncate logs.
# launchd StandardOutPath often truncates the file on each start; we append instead.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="${ROOT}/.venv/bin/python"
WATCH="${ROOT}/scripts/watch_ci_billing.py"
LOG_DIR="${HOME}/Library/Logs/buusdo"
OUT_LOG="${LOG_DIR}/watch-ci-billing.out.log"
ERR_LOG="${LOG_DIR}/watch-ci-billing.err.log"

mkdir -p "${LOG_DIR}"
{
  echo "---- $(date -u +%Y-%m-%dT%H:%M:%SZ) watch_ci_billing ----"
  "${PYTHON}" "${WATCH}" --notify --once --limit 3
  echo "---- exit $? ----"
} >>"${OUT_LOG}" 2>>"${ERR_LOG}"
