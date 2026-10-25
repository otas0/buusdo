#!/usr/bin/env bash
# Local-only codesign hooks. Secrets stay on the builder — never commit them.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIST="${ROOT}/dist"
ARTIFACT="${1:-}"

if [[ -z "${ARTIFACT}" ]]; then
  echo "Usage: $0 <path-to-exe-or-app>" >&2
  exit 2
fi

# Optional local env file (gitignored): scripts/codesign.env
if [[ -f "${ROOT}/scripts/codesign.env" ]]; then
  # shellcheck disable=SC1091
  source "${ROOT}/scripts/codesign.env"
fi

case "$(uname -s)" in
  Darwin)
    : "${CODESIGN_IDENTITY:?Set CODESIGN_IDENTITY in scripts/codesign.env}"
    codesign --deep --force --options runtime --sign "${CODESIGN_IDENTITY}" "${ARTIFACT}"
    if [[ -n "${NOTARY_PROFILE:-}" ]]; then
      ditto -c -k --keepParent "${ARTIFACT}" "${DIST}/buusdo-notarize.zip"
      xcrun notarytool submit "${DIST}/buusdo-notarize.zip" --keychain-profile "${NOTARY_PROFILE}" --wait
      xcrun stapler staple "${ARTIFACT}"
    fi
    ;;
  MINGW*|MSYS*|CYGWIN*|Windows_NT)
    : "${SIGNTOOL:=signtool}"
    "${SIGNTOOL}" sign /fd SHA256 /tr "${TIMESTAMP_URL:-http://timestamp.digicert.com}" /td SHA256 /a "${ARTIFACT}"
    "${SIGNTOOL}" verify /pa "${ARTIFACT}"
    ;;
  *)
    echo "codesign_hooks: unsupported host $(uname -s). Build on Windows/macOS for signing." >&2
    exit 1
    ;;
esac

echo "Signed: ${ARTIFACT}"
