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
  PYTHON="$(command -v python3)"
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

# Three-step end-user install notes (kits remain external).
cat > "${OUT}/INSTALL.txt" <<'EOF'
buusdo — three-step install (MVP)

1. Install Python 3.11+ (Windows: python.org or Store).
2. Install the wheel from this folder, then launch:
     python -m pip install buusdo-*.whl
     python -m pip install "buusdo[ui]"   # if the wheel was built without extras
     # or: uv pip install ./buusdo-*.whl
     python -m buusdo
3. In the UI, pick your ReShade / OptiScaler kit folders (binaries are not bundled).

Windows is the supported MVP platform. Linux and macOS are experimental.
Do not expect DWM HDR injection in this preview (Phase 3).

Verify downloads:
  sha256sum -c SHA256SUMS    # or: shasum -a 256 -c SHA256SUMS
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
