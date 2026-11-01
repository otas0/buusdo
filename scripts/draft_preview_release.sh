#!/usr/bin/env bash
# Create a GitHub *draft* preview Release with Setup + SHA256SUMS (not v1.*).
# Usage (after green installer artifact download into dist/):
#   bash scripts/draft_preview_release.sh [tag]
# Default tag: v0.1.0-installer-preview (never v1.* from this script).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"
TAG="${1:-v0.1.0-installer-preview}"

if [[ "${TAG}" == v1.* || "${TAG}" == 1.* ]]; then
  echo "FATAL: refusing v1.* tag — unsigned Inno smoke + STORE_MVP gate required first." >&2
  exit 1
fi
if [[ "${TAG}" == v0.1.1 || "${TAG}" == 0.1.1 ]]; then
  echo "FATAL: refusing 0.1.1 here — ship 0.1.1 only after launch/scan Issues are fixed." >&2
  exit 1
fi

SETUP="$(ls dist/buusdo-setup-*.exe 2>/dev/null | head -1 || true)"
if [[ -z "${SETUP}" || ! -f dist/SHA256SUMS ]]; then
  echo "FATAL: need dist/buusdo-setup-*.exe and dist/SHA256SUMS (download installer artifact first)." >&2
  exit 1
fi

# PE icon gate when verify script is available.
if [[ -f scripts/verify_pe_icon.py ]]; then
  python3 scripts/verify_pe_icon.py "${SETUP}" || {
    echo "FATAL: Setup.exe missing icon resources — fix Nuitka/Inno icon before drafting." >&2
    exit 1
  }
fi

NOTES="$(mktemp)"
trap 'rm -f "${NOTES}"' EXIT
cat > "${NOTES}" <<EOF
## buusdo installer preview (draft — not v1 / not official)

Unsigned Windows Inno build. SmartScreen may warn. Authenticode deferred.

- Confirm Setup + \`buusdo.exe\` show the wordmark in Explorer.
- Smoke: \`scripts/smoke_windows_install.ps1 -SetupExe dist\\\\buusdo-setup-*.exe\`
- Kits still BYO. No DWM HDR.
- Do **not** promote to \`v1.*\` until STORE_MVP smoke passes.
- Hold \`0.1.1\` until real \`launch\`/\`scan\` Issues are filed and fixed.

Verify: \`shasum -a 256 -c SHA256SUMS\`
EOF

ASSETS=("${SETUP}" dist/SHA256SUMS)
[[ -f dist/INSTALL.txt ]] && ASSETS+=(dist/INSTALL.txt)
# Optional wheel if present
shopt -s nullglob
for w in dist/buusdo-*.whl; do ASSETS+=("${w}"); done

# Prefer attach helper (updates existing draft without publishing).
exec bash "${ROOT}/scripts/attach_installer_to_draft.sh" "${TAG}"
