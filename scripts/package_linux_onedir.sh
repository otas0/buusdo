#!/usr/bin/env bash
# Build an unsigned Linux onedir tarball via PyInstaller.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"

if command -v uv >/dev/null 2>&1; then
  RUN_PY=(uv run python)
  uv sync --extra ui >/dev/null
  uv pip install -q pyinstaller
else
  RUN_PY=(python3)
fi

VER="$("${RUN_PY[@]}" -c "from buusdo import __version__; print(__version__)")"
OUT="${ROOT}/dist"
WORK="${OUT}/.pyi-linux"
DIR="${OUT}/linux"
TAR_NAME="buusdo-linux-${VER}.tar.gz"

rm -rf "${WORK}" "${DIR}"
mkdir -p "${WORK}" "${DIR}"

uv run pyinstaller \
  --noconfirm --clean --onedir \
  --name buusdo \
  --distpath "${DIR}" \
  --workpath "${WORK}" \
  --specpath "${WORK}" \
  --add-data "${ROOT}/buusdo/assets:buusdo/assets" \
  --add-data "${ROOT}/buusdo/locales:buusdo/locales" \
  --hidden-import buusdo \
  "${ROOT}/buusdo/app.py"

"${RUN_PY[@]}" "${ROOT}/scripts/check_pyinstaller_datas.py" "${DIR}/buusdo"

rm -f "${OUT}/${TAR_NAME}"
tar -C "${DIR}" -czf "${OUT}/${TAR_NAME}" buusdo
echo "OK  ${OUT}/${TAR_NAME}"
ls -la "${OUT}/${TAR_NAME}"
