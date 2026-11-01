#!/usr/bin/env bash
# Kick the LaunchAgent once and assert the out log gained an append marker + exit line
# *after* the latest timestamp (stricter than a loose grep of the last 60 lines).
# Does not poll GitHub Actions — LaunchAgent / local log only.
set -euo pipefail

LABEL="com.buusdo.watch-ci-billing"
LOG="${HOME}/Library/Logs/buusdo/watch-ci-billing.out.log"
UID_NUM="$(id -u)"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HELPER="${ROOT}/scripts/watch_ci_billing_log_assert.py"

if [[ ! -f "${LOG}" ]]; then
  echo "missing ${LOG} — run: bash scripts/install_watch_ci_billing_launchd.sh" >&2
  exit 2
fi

_check_append() {
  local before_n="$1"
  python3 -c "
import importlib.util, sys
from pathlib import Path
helper = Path(r'${HELPER}')
spec = importlib.util.spec_from_file_location('watch_ci_billing_log_assert', helper)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)
text = Path(r'${LOG}').read_text(encoding='utf-8', errors='replace')
ok, reason = mod.appended_chunk_ok(text, int('${before_n}'))
if not ok:
    print('FAIL:', reason, file=sys.stderr)
    sys.exit(1)
print(reason)
"
}

before="$(wc -c < "${LOG}" | tr -d ' ')"
launchctl kickstart -k "gui/${UID_NUM}/${LABEL}"
# Wait briefly for the wrapper to append (including ---- exit N ----).
for _ in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do
  sleep 1
  after="$(wc -c < "${LOG}" | tr -d ' ')"
  if (( after > before )) && _check_append "${before}" >/dev/null; then
    break
  fi
done
after="$(wc -c < "${LOG}" | tr -d ' ')"
if (( after <= before )); then
  echo "FAIL: log size did not grow (${before} -> ${after})" >&2
  exit 1
fi
if ! _check_append "${before}"; then
  echo "FAIL: exit marker not after latest timestamp" >&2
  tail -n 40 "${LOG}" >&2 || true
  exit 1
fi
echo "OK: log appended ${before}->${after}; exit marker after latest timestamp"
exit 0
