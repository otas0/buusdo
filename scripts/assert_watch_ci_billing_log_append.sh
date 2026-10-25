#!/usr/bin/env bash
# Kick the LaunchAgent once and assert the out log gained an append marker + exit line.
# Does not poll GitHub Actions — LaunchAgent / local log only.
set -euo pipefail

LABEL="com.buusdo.watch-ci-billing"
LOG="${HOME}/Library/Logs/buusdo/watch-ci-billing.out.log"
UID_NUM="$(id -u)"

if [[ ! -f "${LOG}" ]]; then
  echo "missing ${LOG} — run: bash scripts/install_watch_ci_billing_launchd.sh" >&2
  exit 2
fi

before="$(wc -c < "${LOG}" | tr -d ' ')"
launchctl kickstart -k "gui/${UID_NUM}/${LABEL}"
# Wait briefly for the wrapper to append (including ---- exit N ----).
for _ in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
  sleep 1
  after="$(wc -c < "${LOG}" | tr -d ' ')"
  if (( after > before )) && tail -n 60 "${LOG}" | grep -Eq -- '---- exit [0-9]+ ----'; then
    break
  fi
done
after="$(wc -c < "${LOG}" | tr -d ' ')"
if (( after <= before )); then
  echo "FAIL: log size did not grow (${before} -> ${after})" >&2
  exit 1
fi
if ! tail -n 60 "${LOG}" | grep -Eq -- '---- 20[0-9]{2}-'; then
  echo "FAIL: missing ---- timestamp marker in recent log" >&2
  tail -n 30 "${LOG}" >&2 || true
  exit 1
fi
if ! tail -n 60 "${LOG}" | grep -Eq -- '---- exit [0-9]+ ----'; then
  echo "FAIL: missing ---- exit N ---- marker in recent log" >&2
  tail -n 30 "${LOG}" >&2 || true
  exit 1
fi
echo "OK: log appended ${before}->${after} with timestamp + exit marker"
exit 0
