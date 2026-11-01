#!/usr/bin/env bash
# Windows GitHub installer: deploy payload → Inno Setup → SHA256SUMS.
# Code signing is intentionally skipped (GitHub-only channel).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"
OUT="${ROOT}/dist"
ISS="${ROOT}/packaging/inno/buusdo.iss"
VER="$("${ROOT}/.venv/bin/python" -c "from buusdo import __version__; print(__version__)" 2>/dev/null \
  || python -c "from buusdo import __version__; print(__version__)" 2>/dev/null \
  || echo "0.1.0")"

mkdir -p "${OUT}/payload"

echo "=== 1) App payload (pyside6-deploy) ==="
if command -v pyside6-deploy >/dev/null 2>&1; then
  bash "${ROOT}/scripts/deploy.sh" || true
  # Normalize into dist/payload for Inno.
  if [[ -d "${OUT}/buusdo.dist" ]]; then
    rm -rf "${OUT}/payload"
    mkdir -p "${OUT}/payload"
    cp -R "${OUT}/buusdo.dist/." "${OUT}/payload/"
  elif [[ -f "${OUT}/buusdo.exe" ]]; then
    cp -f "${OUT}/buusdo.exe" "${OUT}/payload/buusdo.exe"
  elif [[ -f "${OUT}/buusdo" ]]; then
    cp -f "${OUT}/buusdo" "${OUT}/payload/buusdo.exe"
  fi
else
  echo "pyside6-deploy not found — writing stub README into payload (CI/docs dry-run)."
  cat > "${OUT}/payload/README-PAYLOAD.txt" <<EOF
Run on a Windows builder with: pip/uv install '.[devui]' and pyside6-deploy on PATH,
then re-run scripts/package_windows_inno.sh so dist/payload contains buusdo.exe.
EOF
fi

echo "=== 2) Inno Setup (unsigned) ==="
ISCC="$(command -v iscc || true)"
if [[ -z "${ISCC}" && -x "/c/Program Files (x86)/Inno Setup 6/ISCC.exe" ]]; then
  ISCC="/c/Program Files (x86)/Inno Setup 6/ISCC.exe"
fi
if [[ -n "${ISCC}" ]]; then
  "${ISCC}" "/DMyAppVersion=${VER}" "${ISS}"
else
  echo "iscc not found — skipping .exe build (script + iss are ready for Windows)."
  echo "Install Inno Setup 6 and re-run on Windows."
fi

echo "=== 3) INSTALL + checksums (no signing) ==="
cat > "${OUT}/INSTALL.txt" <<EOF
buusdo ${VER} — GitHub Windows installer (unsigned)

Supported: Windows 10/11 (x64)
Experimental (no installer): Linux, macOS — source/wheel only

1. Download buusdo-setup-${VER}.exe and SHA256SUMS from the GitHub Release.
2. Verify:  certutil -hashfile buusdo-setup-${VER}.exe SHA256
3. Run the installer (SmartScreen may warn — expected for unsigned GitHub builds).
4. Launch buusdo and select your own ReShade / OptiScaler kit folders.

Not included: Authenticode signature, Microsoft Store package, DWM HDR, bundled kits.
Feedback: https://github.com/otas0/buusdo/issues
EOF

(
  cd "${OUT}"
  if command -v shasum >/dev/null 2>&1; then
    find . -type f ! -name 'SHA256SUMS' ! -name '.gitignore' -print0 | sort -z | xargs -0 shasum -a 256 > SHA256SUMS
  else
    find . -type f ! -name 'SHA256SUMS' ! -name '.gitignore' -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS
  fi
)

echo "Done. Signing skipped (GitHub-only). Artifacts in ${OUT}"
ls -la "${OUT}" || true
