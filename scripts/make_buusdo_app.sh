#!/usr/bin/env bash
# Minimal macOS .app wrapper so Dock / Computer Use can resolve Buusdo.
# Dev-only — not a notarized installer. Does not change draft / Authenticode holds.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP="${ROOT}/dist/Buusdo.app"
MACOS="${APP}/Contents/MacOS"
RES="${APP}/Contents/Resources"
PY="${ROOT}/.venv/bin/python"
ICNS="${ROOT}/buusdo/assets/logo.icns"

if [[ ! -x "${PY}" ]]; then
  echo "Missing ${PY} — run: uv sync --extra ui" >&2
  exit 1
fi

rm -rf "${APP}"
mkdir -p "${MACOS}" "${RES}"

cat > "${MACOS}/Buusdo" <<EOF
#!/bin/bash
cd "${ROOT}"
exec "${PY}" -m buusdo "\$@"
EOF
chmod +x "${MACOS}/Buusdo"

ICON_XML=""
if [[ -f "${ICNS}" ]]; then
  cp "${ICNS}" "${RES}/AppIcon.icns"
  ICON_XML="  <key>CFBundleIconFile</key>
  <string>AppIcon</string>"
fi

cat > "${APP}/Contents/Info.plist" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleExecutable</key>
  <string>Buusdo</string>
  <key>CFBundleIdentifier</key>
  <string>app.buusdo.dev</string>
  <key>CFBundleName</key>
  <string>Buusdo</string>
  <key>CFBundleDisplayName</key>
  <string>Buusdo</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>CFBundleShortVersionString</key>
  <string>0.1.0</string>
  <key>LSMinimumSystemVersion</key>
  <string>12.0</string>
  <key>NSHighResolutionCapable</key>
  <true/>
${ICON_XML}
</dict>
</plist>
PLIST

echo "OK  ${APP}"
echo "Launch: open ${APP}"
echo "Hold: not an installer preview / no tag / Authenticode still off."
