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

# Optional local codesign (scripts/codesign.env must exist; never committed).
if [[ "${BUUSDO_CODESIGN:-}" == "1" ]] || [[ -f "${ROOT}/scripts/codesign.env" ]]; then
  HOOK="${ROOT}/scripts/codesign_hooks.sh"
  if [[ -x "${HOOK}" ]]; then
    signed_any=0
    failed_paths=()
    unsigned_candidates=()
    while IFS= read -r art; do
      [[ -z "${art}" ]] && continue
      unsigned_candidates+=("${art}")
      echo "codesign: signing ${art}"
      if ! "${HOOK}" "${art}"; then
        echo "codesign: hook failed for ${art}" >&2
        failed_paths+=("${art}")
        if [[ "${BUUSDO_CODESIGN_STRICT:-}" != "1" ]]; then
          echo "codesign: continuing (set BUUSDO_CODESIGN_STRICT=1 to fail the build)" >&2
        fi
      else
        signed_any=1
      fi
    done < <(find "${OUT}" -maxdepth 3 \( -name 'buusdo' -o -name 'buusdo.exe' -o -name 'buusdo.app' \) 2>/dev/null | head -5)
    if [[ "${signed_any}" -eq 0 && ${#unsigned_candidates[@]} -eq 0 ]]; then
      echo "codesign: no buusdo artifact found under ${OUT}; skip."
      if [[ "${BUUSDO_CODESIGN_STRICT:-}" == "1" ]]; then
        echo "codesign: strict mode — unsigned path list:" >&2
        find "${OUT}" -maxdepth 4 -type f 2>/dev/null | head -50 >&2 || true
        exit 1
      fi
    fi
    if [[ ${#failed_paths[@]} -gt 0 && "${BUUSDO_CODESIGN_STRICT:-}" == "1" ]]; then
      echo "codesign: strict mode — failed to sign:" >&2
      printf '  %s\n' "${failed_paths[@]}" >&2
      echo "codesign: remaining candidates under dist:" >&2
      printf '  %s\n' "${unsigned_candidates[@]}" >&2
      exit 1
    fi
  fi
fi
