#!/usr/bin/env bash
# Sign + notarize + staple a macOS .app, then emit a release zip.
#
# Prerequisites (local only — never commit secrets):
#   1. Apple Developer Program membership
#   2. "Developer ID Application" cert installed in login keychain
#      (security find-identity -v -p codesigning)
#   3. notarytool keychain profile, e.g.:
#        xcrun notarytool store-credentials "buusdo-notary" \
#          --apple-id "you@example.com" --team-id "TEAMID" --password "app-specific-password"
#   4. scripts/codesign.env (gitignored):
#        CODESIGN_IDENTITY="Developer ID Application: Your Name (TEAMID)"
#        NOTARY_PROFILE="buusdo-notary"
#
# Usage:
#   bash scripts/sign_and_notarize_macos.sh [path/to/Buusdo.app]
# If omitted, builds via package_macos_bundle.sh then signs the unzipped .app.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "${ROOT}"
DIST="${ROOT}/dist"
ENV_FILE="${ROOT}/scripts/codesign.env"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "FATAL: missing ${ENV_FILE}" >&2
  echo "Copy scripts/codesign.env.example → scripts/codesign.env and fill real values." >&2
  exit 1
fi
# shellcheck disable=SC1090
source "${ENV_FILE}"
: "${CODESIGN_IDENTITY:?Set CODESIGN_IDENTITY in scripts/codesign.env}"
: "${NOTARY_PROFILE:?Set NOTARY_PROFILE in scripts/codesign.env}"

if ! security find-identity -v -p codesigning | grep -F "${CODESIGN_IDENTITY}" >/dev/null; then
  echo "FATAL: identity not found in keychain:" >&2
  echo "  ${CODESIGN_IDENTITY}" >&2
  echo "Install Developer ID Application from developer.apple.com → Certificates." >&2
  security find-identity -v -p codesigning >&2 || true
  exit 1
fi

APP="${1:-}"
if [[ -z "${APP}" ]]; then
  bash "${ROOT}/scripts/package_macos_bundle.sh"
  VER="$(python3 -c "from buusdo import __version__; print(__version__)" 2>/dev/null \
    || "${ROOT}/.venv/bin/python" -c "from buusdo import __version__; print(__version__)")"
  ZIP_SRC="${DIST}/buusdo-macos-${VER}.zip"
  STAGE="${DIST}/macos-sign-stage"
  rm -rf "${STAGE}"
  mkdir -p "${STAGE}"
  unzip -q "${ZIP_SRC}" -d "${STAGE}"
  APP="$(find "${STAGE}" -maxdepth 2 -name '*.app' -type d | head -1)"
fi

if [[ -z "${APP}" || ! -d "${APP}" ]]; then
  echo "FATAL: .app not found" >&2
  exit 1
fi

APP="$(cd "$(dirname "${APP}")" && pwd)/$(basename "${APP}")"
VER="$(python3 -c "from buusdo import __version__; print(__version__)" 2>/dev/null \
  || "${ROOT}/.venv/bin/python" -c "from buusdo import __version__; print(__version__)")"
OUT_ZIP="${DIST}/buusdo-macos-${VER}.zip"
NOTARY_ZIP="${DIST}/buusdo-notarize-${VER}.zip"

echo "==> codesign (Developer ID, hardened runtime)"
# Clear quarantine before signing
xattr -cr "${APP}" || true
codesign --deep --force --options runtime --timestamp \
  --sign "${CODESIGN_IDENTITY}" \
  "${APP}"
codesign --verify --deep --strict --verbose=2 "${APP}"

echo "==> notarize (notarytool profile=${NOTARY_PROFILE})"
rm -f "${NOTARY_ZIP}"
ditto -c -k --keepParent "${APP}" "${NOTARY_ZIP}"
xcrun notarytool submit "${NOTARY_ZIP}" \
  --keychain-profile "${NOTARY_PROFILE}" \
  --wait

echo "==> staple"
xcrun stapler staple "${APP}"
xcrun stapler validate "${APP}"

echo "==> Gatekeeper assess"
spctl --assess --type execute --verbose "${APP}" || {
  echo "WARN: spctl assess reported issues (may still open after staple on fresh download)" >&2
}

echo "==> release zip"
rm -f "${OUT_ZIP}"
(
  cd "$(dirname "${APP}")"
  zip -qry "${OUT_ZIP}" "$(basename "${APP}")"
)
rm -f "${NOTARY_ZIP}"

echo "OK  signed+notarized+stapled → ${OUT_ZIP}"
echo "Next: replace the GitHub Release asset and refresh SHA256SUMS:"
echo "  gh release upload v${VER} ${OUT_ZIP} --clobber"
echo "  (rebuild SHA256SUMS for all assets, upload, keep release published)"
