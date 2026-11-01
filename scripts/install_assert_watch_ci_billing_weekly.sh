#!/usr/bin/env bash
# Optional weekly LaunchAgent: Monday 09:00 local — assert watch-ci-billing log append.
# LaunchAgent / local log only — does not poll GitHub Actions.
# Usage:
#   bash scripts/install_assert_watch_ci_billing_weekly.sh
#   bash scripts/install_assert_watch_ci_billing_weekly.sh --uninstall
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LABEL="com.buusdo.assert-watch-ci-billing-weekly"
PLIST="$HOME/Library/LaunchAgents/${LABEL}.plist"
ASSERT="${ROOT}/scripts/assert_watch_ci_billing_log_append.sh"
LOG_DIR="${HOME}/Library/Logs/buusdo"
mkdir -p "${LOG_DIR}"
chmod +x "${ASSERT}"

if [[ "${1:-}" == "--uninstall" ]]; then
  launchctl bootout "gui/$(id -u)/${LABEL}" 2>/dev/null || true
  rm -f "${PLIST}"
  echo "Removed ${PLIST}"
  exit 0
fi

if [[ ! -f "${ASSERT}" ]]; then
  echo "Missing ${ASSERT}" >&2
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
    <string>${ASSERT}</string>
  </array>
  <key>WorkingDirectory</key>
  <string>${ROOT}</string>
  <key>StartCalendarInterval</key>
  <dict>
    <key>Weekday</key>
    <integer>1</integer>
    <key>Hour</key>
    <integer>9</integer>
    <key>Minute</key>
    <integer>0</integer>
  </dict>
  <key>StandardOutPath</key>
  <string>${LOG_DIR}/assert-weekly.out.log</string>
  <key>StandardErrorPath</key>
  <string>${LOG_DIR}/assert-weekly.err.log</string>
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
echo "Installed ${PLIST} (Monday 09:00 local)."
echo "Logs: ${LOG_DIR}/assert-weekly.*.log"
echo "Uninstall: bash scripts/install_assert_watch_ci_billing_weekly.sh --uninstall"
echo "# crontab alternative:"
echo "0 9 * * 1 cd ${ROOT} && bash scripts/assert_watch_ci_billing_log_append.sh >>${LOG_DIR}/assert-cron.log 2>&1"
