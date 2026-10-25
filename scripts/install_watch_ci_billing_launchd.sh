#!/usr/bin/env bash
# Install a per-user launchd agent that runs watch_ci_billing.py hourly.
# Usage:
#   bash scripts/install_watch_ci_billing_launchd.sh
#   bash scripts/install_watch_ci_billing_launchd.sh --uninstall
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LABEL="com.buusdo.watch-ci-billing"
PLIST="$HOME/Library/LaunchAgents/${LABEL}.plist"
PYTHON="${ROOT}/.venv/bin/python"
WATCH="${ROOT}/scripts/watch_ci_billing.py"
LOG_DIR="${HOME}/Library/Logs/buusdo"
mkdir -p "${LOG_DIR}"

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
    <string>${PYTHON}</string>
    <string>${WATCH}</string>
    <string>--notify</string>
    <string>--once</string>
    <string>--limit</string>
    <string>3</string>
  </array>
  <key>WorkingDirectory</key>
  <string>${ROOT}</string>
  <key>StartInterval</key>
  <integer>3600</integer>
  <key>RunAtLoad</key>
  <true/>
  <key>StandardOutPath</key>
  <string>${LOG_DIR}/watch-ci-billing.out.log</string>
  <key>StandardErrorPath</key>
  <string>${LOG_DIR}/watch-ci-billing.err.log</string>
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
echo "Installed ${PLIST} (hourly --notify --once)."
echo "Logs: ${LOG_DIR}/watch-ci-billing.*.log"
echo "Uninstall: bash scripts/install_watch_ci_billing_launchd.sh --uninstall"
# Also print a crontab-equivalent for Linux/docs.
echo "# crontab alternative (hourly):"
echo "0 * * * * cd ${ROOT} && ${PYTHON} ${WATCH} --notify --once >> ${LOG_DIR}/watch-ci-billing.cron.log 2>&1"
