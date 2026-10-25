#!/usr/bin/env bash
# Finite-retry git push for flaky GitHub HTTPS CONNECT.
# Usage:
#   bash scripts/push_when_online.sh
#   bash scripts/push_when_online.sh main phase3/dwm-hdr
#   MAX_TRIES=8 SLEEP_S=10 bash scripts/push_when_online.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"

MAX_TRIES="${MAX_TRIES:-6}"
SLEEP_S="${SLEEP_S:-10}"
BRANCHES=("$@")
if [[ ${#BRANCHES[@]} -eq 0 ]]; then
  BRANCHES=(main phase3/dwm-hdr)
fi

push_one() {
  local branch="$1"
  local i
  for ((i = 1; i <= MAX_TRIES; i++)); do
    echo "push ${branch} try ${i}/${MAX_TRIES}"
    if git push origin "${branch}"; then
      echo "pushed ${branch}"
      return 0
    fi
    if ((i < MAX_TRIES)); then
      sleep "${SLEEP_S}"
    fi
  done
  echo "FAILED to push ${branch} after ${MAX_TRIES} tries" >&2
  return 1
}

rc=0
for b in "${BRANCHES[@]}"; do
  push_one "${b}" || rc=1
done
exit "${rc}"
