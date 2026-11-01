#!/usr/bin/env bash
# Attach dist Setup + SHA256SUMS (+ optional INSTALL/wheel) to the draft preview release.
# Never publishes. Never creates v1.* or 0.1.1.
# Usage:
#   bash scripts/attach_installer_to_draft.sh [tag]
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"
TAG="${1:-v0.1.0-installer-preview}"

if [[ "${TAG}" == v1.* || "${TAG}" == 1.* ]]; then
  echo "FATAL: refusing v1.* — keep draft unpublished; Authenticode/Explorer smoke first." >&2
  exit 1
fi
if [[ "${TAG}" == v0.1.1 || "${TAG}" == 0.1.1 ]]; then
  echo "FATAL: refusing 0.1.1 — hold until launch/scan Issues are fixed." >&2
  exit 1
fi

SETUP="$(ls dist/buusdo-setup-*.exe 2>/dev/null | head -1 || true)"
if [[ -z "${SETUP}" || ! -f dist/SHA256SUMS ]]; then
  echo "FATAL: need dist/buusdo-setup-*.exe and dist/SHA256SUMS" >&2
  exit 1
fi

_py() {
  if command -v uv >/dev/null 2>&1; then
    uv run python "$@"
  elif command -v python3 >/dev/null 2>&1; then
    python3 "$@"
  else
    python "$@"
  fi
}
if [[ -f scripts/verify_pe_icon.py ]]; then
  _py scripts/verify_pe_icon.py "${SETUP}"
  if [[ -f dist/payload/buusdo.exe ]]; then
    _py scripts/verify_pe_icon.py dist/payload/buusdo.exe
  fi
fi

ASSETS=("${SETUP}" dist/SHA256SUMS)
[[ -f dist/INSTALL.txt ]] && ASSETS+=(dist/INSTALL.txt)
shopt -s nullglob
for w in dist/buusdo-*.whl; do ASSETS+=("${w}"); done

NOTES="$(mktemp)"
trap 'rm -f "${NOTES}"' EXIT
cat > "${NOTES}" <<EOF
## buusdo installer preview (draft — not v1 / not official)

Unsigned Windows Inno build. SmartScreen may warn. **Authenticode deferred** until Explorer wordmark smoke on Setup + \`buusdo.exe\`.

### Gates
- PE icons verified (\`scripts/verify_pe_icon.py\` — RT_ICON / RT_GROUP_ICON)
- Hold \`0.1.1\` until real \`launch\` / \`scan\` Issues are filed and fixed
- Icon-missing-after-install → label \`launch\` before any feature work
- Phase 3 DWM HDR stays on \`phase3/dwm-hdr\` (default branch is \`main\`)
- Do **not** tag \`v1.*\`; keep this release **draft** until a human promotes a preview (still not v1)

### Promote to published preview (optional, still not v1)
Only after: Explorer shows the wordmark on Setup + \`buusdo.exe\`, and smoke is OK.
Then: \`gh release edit ${TAG} --draft=false\` (never retitle as v1).

Verify: \`shasum -a 256 -c SHA256SUMS\`
EOF

if gh release view "${TAG}" >/dev/null 2>&1; then
  echo "Updating existing draft ${TAG}…"
  gh release upload "${TAG}" "${ASSETS[@]}" --clobber
  gh release edit "${TAG}" --draft=true --notes-file "${NOTES}" \
    --title "buusdo ${TAG} (installer preview draft)"
else
  echo "Creating draft ${TAG}…"
  gh release create "${TAG}" "${ASSETS[@]}" \
    --draft \
    --title "buusdo ${TAG} (installer preview draft)" \
    --notes-file "${NOTES}"
fi

# Hard assert: must remain draft
IS_DRAFT="$(gh release view "${TAG}" --json isDraft -q .isDraft)"
if [[ "${IS_DRAFT}" != "true" ]]; then
  echo "FATAL: release left non-draft — forcing draft again" >&2
  gh release edit "${TAG}" --draft=true
fi
echo "OK  draft ${TAG} has Setup + SHA256SUMS (unpublished)."
gh release view "${TAG}" --json url,isDraft,tagName,assets -q '{url,isDraft,tagName,assets:[.assets[].name]}'
