#!/usr/bin/env bash
# Install a per-user launchd agent that runs watch_ci_billing.py hourly.
# Usage:
#   bash scripts/install_watch_ci_billing_launchd.sh
#   bash scripts/install_watch_ci_billing_launchd.sh --uninstall
#
# Logging: uses scripts/run_watch_ci_billing_launchd.sh so each run *appends*
# to ~/Library/Logs/buusdo/watch-ci-billing.*.log (launchd StandardOutPath truncates).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LABEL="com.buusdo.watch-ci-billing"
PLIST="$HOME/Library/LaunchAgents/${LABEL}.plist"
PYTHON="${ROOT}/.venv/bin/python"
WATCH="${ROOT}/scripts/watch_ci_billing.py"
WRAPPER="${ROOT}/scripts/run_watch_ci_billing_launchd.sh"
LOG_DIR="${HOME}/Library/Logs/buusdo"
mkdir -p "${LOG_DIR}"
chmod +x "${WRAPPER}"

if [[ "${1:-}" == "--uninstall" ]]; then
  launchctl bootout "gui/$(id -u)/${LABEL}" 2>/dev/null || true
  rm -f "${PLIST}"
  echo "Removed ${PLIST}"
  exit 0
fi

if [[ ! -x "${PYTHON}" ]]; then
  echo "Missing ${PYTHON} — create .venv and pip install -e .[dev] first" >&2
  exit 1
fi
if [[ ! -f "${WATCH}" ]]; then
  echo "Missing ${WATCH}" >&2
  exit 1
fi

cat > "${PLIST}" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>${WRAPPER}</string>
  </array>
  <key>WorkingDirectory</key>
  <string>${ROOT}</string>
  <key>StartInterval</key>
  <integer>3600</integer>
  <key>RunAtLoad</key>
  <true/>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
  </dict>
</dict>
</plist>
EOF

launchctl bootout "gui/$(id -u)/${LABEL}" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "${PLIST}"
launchctl enable "gui/$(id -u)/${LABEL}" 2>/dev/null || true
echo "Installed ${PLIST} (hourly; append logs via ${WRAPPER})."
echo "Logs: ${LOG_DIR}/watch-ci-billing.*.log"
echo "Kick once: launchctl kickstart -k gui/\$(id -u)/${LABEL}"
echo "Uninstall: bash scripts/install_watch_ci_billing_launchd.sh --uninstall"
echo "# crontab alternative (hourly, also appends):"
echo "0 * * * * ${WRAPPER}"
