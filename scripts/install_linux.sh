#!/usr/bin/env bash
# Linux installer helper: create a user venv and install the adjacent wheel + UI deps.
# Usage (from the extracted release dir or next to the wheel):
#   bash install_linux.sh
#   bash install_linux.sh /path/to/buusdo-*-py3-none-any.whl
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
WHEEL="${1:-}"
if [[ -z "${WHEEL}" ]]; then
  WHEEL="$(ls "${ROOT}"/buusdo-*-py3-none-any.whl 2>/dev/null | head -1 || true)"
fi
if [[ -z "${WHEEL}" || ! -f "${WHEEL}" ]]; then
  echo "FATAL: pass a wheel path or place buusdo-*-py3-none-any.whl next to this script" >&2
  exit 1
fi

VENV="${HOME}/.local/share/buusdo/venv"
BIN="${HOME}/.local/bin"
mkdir -p "${VENV%/*}" "${BIN}"

python3 -m venv "${VENV}"
# shellcheck disable=SC1091
source "${VENV}/bin/activate"
python -m pip install -U pip
python -m pip install "${WHEEL}" "PySide6-Essentials==6.12.0"
deactivate

WRAPPER="${BIN}/buusdo"
cat > "${WRAPPER}" <<EOF
#!/usr/bin/env bash
exec "${VENV}/bin/python" -m buusdo "\$@"
EOF
chmod +x "${WRAPPER}"

echo "OK  installed ${WHEEL}"
echo "    launcher: ${WRAPPER}"
echo "    run: buusdo   (ensure ${BIN} is on PATH)"
echo "    kits (ReShade / OptiScaler) are BYO — not bundled"
echo "    unsigned build — no code signing"
