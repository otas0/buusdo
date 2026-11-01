#!/usr/bin/env bash
# Windows GitHub installer: deploy payload → Inno Setup → SHA256SUMS.
# Code signing intentionally skipped (GitHub-only channel).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"
OUT="${ROOT}/dist"
ISS="${ROOT}/packaging/inno/buusdo.iss"
PY="${ROOT}/.venv/bin/python"
if [[ ! -x "${PY}" ]]; then
  PY="${ROOT}/.venv/Scripts/python.exe"
fi
if [[ ! -x "${PY}" ]]; then
  PY="$(command -v python || command -v python3)"
fi
VER="$("${PY}" -c "from buusdo import __version__; print(__version__)" 2>/dev/null || echo "0.1.0")"

mkdir -p "${OUT}/payload"
export PATH="${ROOT}/.venv/bin:${ROOT}/.venv/Scripts:${PATH:-}"

echo "=== 1) App payload (pyside6-deploy) ==="
DEPLOY_BIN="$(command -v pyside6-deploy || true)"
if [[ -z "${DEPLOY_BIN}" && -x "${ROOT}/.venv/Scripts/pyside6-deploy.exe" ]]; then
  DEPLOY_BIN="${ROOT}/.venv/Scripts/pyside6-deploy.exe"
fi
if [[ -z "${DEPLOY_BIN}" && -x "${ROOT}/.venv/bin/pyside6-deploy" ]]; then
  DEPLOY_BIN="${ROOT}/.venv/bin/pyside6-deploy"
fi

if [[ -n "${DEPLOY_BIN}" ]]; then
  bash "${ROOT}/scripts/deploy.sh" || true
  # Normalize into dist/payload for Inno.
  if [[ -d "${OUT}/buusdo.dist" ]]; then
    rm -rf "${OUT}/payload"
    mkdir -p "${OUT}/payload"
    cp -R "${OUT}/buusdo.dist/." "${OUT}/payload/" || true
  fi
  # Nuitka/pyside6-deploy layouts vary; gather buusdo.exe if present anywhere under dist/.
  if [[ ! -f "${OUT}/payload/buusdo.exe" ]]; then
    found="$(find "${OUT}" -maxdepth 3 -iname 'buusdo.exe' 2>/dev/null | head -1 || true)"
    if [[ -n "${found}" ]]; then
      mkdir -p "${OUT}/payload"
      cp -f "${found}" "${OUT}/payload/buusdo.exe"
      # Copy sibling runtime files if exe lives in a folder.
      parent="$(dirname "${found}")"
      if [[ "${parent}" != "${OUT}/payload" ]]; then
        cp -R "${parent}/." "${OUT}/payload/" 2>/dev/null || true
      fi
    fi
  fi
else
  echo "pyside6-deploy not found — stub payload (CI should install .[devui] first)."
  echo "Run: uv sync --extra devui" > "${OUT}/payload/README-PAYLOAD.txt"
fi

if [[ ! -f "${OUT}/payload/buusdo.exe" ]]; then
  echo "WARN: dist/payload/buusdo.exe missing — Inno may fail until deploy succeeds." >&2
fi

echo "=== 2) Inno Setup (unsigned) ==="
ISCC="$(command -v iscc || true)"
# Common Windows / GitHub Actions paths
for cand in \
  "/c/Program Files (x86)/Inno Setup 6/ISCC.exe" \
  "/c/Program Files/Inno Setup 6/ISCC.exe" \
  "C:/Program Files (x86)/Inno Setup 6/ISCC.exe" \
  "C:/Program Files/Inno Setup 6/ISCC.exe"
do
  if [[ -z "${ISCC}" && -x "${cand}" ]]; then
    ISCC="${cand}"
  fi
done

# Ensure Windows installer icon exists.
if [[ ! -f "${ROOT}/buusdo/assets/logo.ico" ]]; then
  "${PY}" "${ROOT}/scripts/generate_logo_ico.py" || true
fi

if [[ -n "${ISCC}" && -f "${OUT}/payload/buusdo.exe" ]]; then
  "${ISCC}" "/DMyAppVersion=${VER}" "${ISS}"
elif [[ -n "${ISCC}" ]]; then
  echo "iscc found but payload missing — skip setup.exe" >&2
else
  echo "iscc not found — install Inno Setup 6 (choco install innosetup) on Windows."
fi

echo "=== 3) INSTALL + checksums (no signing) ==="
SETUP_NAME="buusdo-setup-${VER}.exe"
cat > "${OUT}/INSTALL.txt" <<EOF
buusdo ${VER} — GitHub Windows build (unsigned)

Wheel (any OS):
  pip install buusdo-*-py3-none-any.whl PySide6-Essentials==6.12.0
  python -m buusdo

Installer (Windows, if ${SETUP_NAME} attached):
  Run ${SETUP_NAME} (SmartScreen may warn — expected, unsigned).
  Then pick your own ReShade/OptiScaler kit folders in the UI.

Windows-first. Linux/macOS experimental. No DWM HDR. Kits not bundled.
Feedback: https://github.com/otas0/buusdo/issues
EOF

(
  cd "${OUT}"
  : > SHA256SUMS
  while IFS= read -r f; do
    [[ -z "${f}" ]] && continue
    base="$(basename "${f}")"
    [[ "${base}" == "SHA256SUMS" || "${base}" == ".gitignore" ]] && continue
    [[ "${f}" == ./payload/* ]] && continue
    if command -v shasum >/dev/null 2>&1; then
      shasum -a 256 "${f}" >> SHA256SUMS
    elif command -v sha256sum >/dev/null 2>&1; then
      sha256sum "${f}" >> SHA256SUMS
    fi
  done < <(find . -type f | sort)
)

echo "Done. Signing skipped. Artifacts in ${OUT}"
ls -la "${OUT}" || true
