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

# Payload backend: pyinstaller (default, icon= reliable on CI) or nuitka (pyside6-deploy).
PAYLOAD_BACKEND="${BUUSDO_PAYLOAD_BACKEND:-pyinstaller}"
echo "=== 1) App payload (backend=${PAYLOAD_BACKEND}) ==="

_build_pyinstaller_payload() {
  echo "Building onefile via PyInstaller (icon=logo.ico)…"
  if command -v uv >/dev/null 2>&1; then
    uv pip install -q pyinstaller
    uv run pyinstaller "${ROOT}/packaging/pyinstaller_buusdo.spec" \
      --distpath "${OUT}/payload" --workpath "${OUT}/.pyi-work" --noconfirm
  else
    "${PY}" -m pip install -q pyinstaller
    "${PY}" -m PyInstaller "${ROOT}/packaging/pyinstaller_buusdo.spec" \
      --distpath "${OUT}/payload" --workpath "${OUT}/.pyi-work" --noconfirm
  fi
}

_build_nuitka_payload() {
  DEPLOY_BIN="$(command -v pyside6-deploy || true)"
  if [[ -z "${DEPLOY_BIN}" && -x "${ROOT}/.venv/Scripts/pyside6-deploy.exe" ]]; then
    DEPLOY_BIN="${ROOT}/.venv/Scripts/pyside6-deploy.exe"
  fi
  if [[ -z "${DEPLOY_BIN}" && -x "${ROOT}/.venv/bin/pyside6-deploy" ]]; then
    DEPLOY_BIN="${ROOT}/.venv/bin/pyside6-deploy"
  fi
  if [[ -z "${DEPLOY_BIN}" ]]; then
    echo "pyside6-deploy not found" >&2
    return 1
  fi
  bash "${ROOT}/scripts/deploy.sh" || true
  if [[ -d "${OUT}/buusdo.dist" ]]; then
    rm -rf "${OUT}/payload"
    mkdir -p "${OUT}/payload"
    cp -R "${OUT}/buusdo.dist/." "${OUT}/payload/" || true
  fi
  if [[ ! -f "${OUT}/payload/buusdo.exe" ]]; then
    found="$(find "${OUT}" -maxdepth 3 -iname 'buusdo.exe' 2>/dev/null | head -1 || true)"
    if [[ -n "${found}" ]]; then
      mkdir -p "${OUT}/payload"
      cp -f "${found}" "${OUT}/payload/buusdo.exe"
      parent="$(dirname "${found}")"
      if [[ "${parent}" != "${OUT}/payload" ]]; then
        cp -R "${parent}/." "${OUT}/payload/" 2>/dev/null || true
      fi
    fi
  fi
}

if [[ "${PAYLOAD_BACKEND}" == "nuitka" ]]; then
  _build_nuitka_payload || true
  if [[ ! -f "${OUT}/payload/buusdo.exe" ]]; then
    echo "Nuitka payload missing — falling back to PyInstaller." >&2
    _build_pyinstaller_payload || true
  fi
else
  _build_pyinstaller_payload || true
  if [[ ! -f "${OUT}/payload/buusdo.exe" ]]; then
    echo "PyInstaller payload missing — trying Nuitka/pyside6-deploy." >&2
    _build_nuitka_payload || true
  fi
fi

if [[ ! -f "${OUT}/payload/buusdo.exe" ]]; then
  found="$(find "${OUT}/payload" -maxdepth 2 -iname 'buusdo.exe' 2>/dev/null | head -1 || true)"
  if [[ -n "${found}" && "${found}" != "${OUT}/payload/buusdo.exe" ]]; then
    cp -f "${found}" "${OUT}/payload/buusdo.exe"
  fi
fi
if [[ ! -f "${OUT}/payload/buusdo.exe" ]]; then
  echo "WARN: dist/payload/buusdo.exe still missing — Inno will skip setup.exe." >&2
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

# Hard gate: Windows packaging never ships without logo.ico (Setup + exe icon source).
ICO="${ROOT}/buusdo/assets/logo.ico"
if [[ -f "${ICO}" ]]; then
  ICO_BYTES="$(wc -c < "${ICO}" | tr -d ' ')"
  if [[ "${ICO_BYTES}" -le 50 || "${ICO_BYTES}" -gt 96000 ]]; then
    if command -v uv >/dev/null 2>&1; then
      uv run python "${ROOT}/scripts/generate_logo_ico.py"
    else
      "${PY}" "${ROOT}/scripts/generate_logo_ico.py"
    fi
  else
    echo "logo.ico present (${ICO_BYTES} bytes) — skip regenerate"
  fi
else
  if command -v uv >/dev/null 2>&1; then
    uv run python "${ROOT}/scripts/generate_logo_ico.py"
  else
    "${PY}" "${ROOT}/scripts/generate_logo_ico.py"
  fi
fi
if [[ ! -f "${ICO}" ]]; then
  echo "FATAL: buusdo/assets/logo.ico missing — refusing Inno / payload package." >&2
  exit 1
fi
echo "logo.ico OK ($(wc -c < "${ICO}" | tr -d ' ') bytes)"

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
