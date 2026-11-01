#!/usr/bin/env bash
# Build MVP distributables: wheel/sdist + SHA256SUMS + INSTALL.txt.
# Optional: also run scripts/deploy.sh when pyside6-deploy is available.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"
OUT="${ROOT}/dist"
mkdir -p "${OUT}"

PYTHON="${ROOT}/.venv/bin/python"
if [[ ! -x "${PYTHON}" ]]; then
  PYTHON="${ROOT}/.venv/Scripts/python.exe"
fi
if [[ ! -x "${PYTHON}" ]]; then
  PYTHON="$(command -v python3 || command -v python || true)"
fi
# Prefer uv-run so Windows CI always sees the synced env (PySide6).
if command -v uv >/dev/null 2>&1; then
  RUN_PY=(uv run python)
elif [[ -n "${PYTHON}" ]]; then
  RUN_PY=("${PYTHON}")
else
  echo "FATAL: no Python interpreter found" >&2
  exit 1
fi

echo "Ensuring logo.ico (Windows exe / Inno / wheel asset)…"
if [[ ! -f "${ROOT}/buusdo/assets/logo.png" ]]; then
  echo "FATAL: buusdo/assets/logo.png missing" >&2
  exit 1
fi
ICO="${ROOT}/buusdo/assets/logo.ico"
ICO_OK=0
if [[ -f "${ICO}" ]]; then
  ICO_BYTES="$(wc -c < "${ICO}" | tr -d ' ')"
  if [[ "${ICO_BYTES}" -gt 50 && "${ICO_BYTES}" -le 96000 ]]; then
    echo "logo.ico already present (${ICO_BYTES} bytes) — skip regenerate"
    ICO_OK=1
  fi
fi
if [[ "${ICO_OK}" -ne 1 ]]; then
  "${RUN_PY[@]}" "${ROOT}/scripts/generate_logo_ico.py"
fi
if [[ ! -f "${ICO}" ]]; then
  echo "FATAL: logo.ico missing after generate_logo_ico.py" >&2
  exit 1
fi
# Best-effort macOS Dock icon when packaging on Darwin (non-fatal elsewhere).
if [[ "$(uname -s)" == "Darwin" ]]; then
  "${RUN_PY[@]}" "${ROOT}/scripts/generate_logo_icns.py" || true
fi

echo "Building wheel/sdist…"
if command -v uv >/dev/null 2>&1; then
  uv build --out-dir "${OUT}"
elif "${PYTHON}" -c "import build" 2>/dev/null; then
  "${PYTHON}" -m build --outdir "${OUT}"
else
  "${PYTHON}" -m pip install -q build
  "${PYTHON}" -m build --outdir "${OUT}"
fi

# End-user install notes (kits remain external). Keep PySide6 on one line.
cat > "${OUT}/INSTALL.txt" <<'EOF'
buusdo preview — install

  pip install buusdo-*-py3-none-any.whl "PySide6-Essentials==6.12.0"
  python -m buusdo

Then pick your own ReShade/OptiScaler kit folders in the UI (not bundled).

Windows-first. Linux/macOS experimental. No official installer in wheel-only tags.
No DWM HDR (Phase 3). Not v1 / not an official release.

Verify: shasum -a 256 -c SHA256SUMS
EOF

# Checksums for all files currently in dist/ (except SHA256SUMS itself).
(
  cd "${OUT}"
  : > SHA256SUMS
  while IFS= read -r f; do
    [[ -z "${f}" ]] && continue
    base="$(basename "${f}")"
    [[ "${base}" == "SHA256SUMS" || "${base}" == ".gitignore" ]] && continue
    # Skip nested payload stubs from other packaging scripts.
    [[ "${f}" == ./payload/* ]] && continue
    if command -v shasum >/dev/null 2>&1; then
      shasum -a 256 "${f}" >> SHA256SUMS
    else
      sha256sum "${f}" >> SHA256SUMS
    fi
  done < <(find . -type f | sort)
)

echo "Wrote ${OUT}/INSTALL.txt and ${OUT}/SHA256SUMS"

# Optional native binary packaging (best-effort; does not fail MVP).
if command -v pyside6-deploy >/dev/null 2>&1; then
  echo "pyside6-deploy found — attempting scripts/deploy.sh (best-effort)…"
  if bash "${ROOT}/scripts/deploy.sh"; then
    (
      cd "${OUT}"
      if command -v shasum >/dev/null 2>&1; then
        find . -type f ! -name 'SHA256SUMS' -print0 | sort -z | xargs -0 shasum -a 256 > SHA256SUMS
      else
        find . -type f ! -name 'SHA256SUMS' -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS
      fi
    )
  else
    echo "deploy.sh failed; wheel/sdist MVP package still valid." >&2
  fi
else
  echo "pyside6-deploy not on PATH — skipping native binary (wheel MVP is enough)."
fi

echo "MVP package ready under ${OUT}"
ls -la "${OUT}"
