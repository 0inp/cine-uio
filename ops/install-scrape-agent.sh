#!/usr/bin/env bash
#
# Install (or remove) the launchd agent that refreshes screenings once a day.
#
#   ./ops/install-scrape-agent.sh            # install, runs daily at 05:00
#   ./ops/install-scrape-agent.sh 7 30       # install, runs daily at 07:30
#   ./ops/install-scrape-agent.sh --uninstall
#
# The plist is generated rather than committed, because it has to carry absolute
# paths to this checkout and to mise, which differ per machine.
#
# If the laptop is asleep or off at the scheduled time, launchd runs the job at the
# next opportunity instead of skipping the day.

set -euo pipefail

LABEL="dev.cine-uio.scrape"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
LOG_DIR="$HOME/Library/Logs/cine-uio"
LOG_FILE="$LOG_DIR/scrape.log"
DOMAIN="gui/$(id -u)"

unload_if_loaded() {
  if launchctl print "$DOMAIN/$LABEL" >/dev/null 2>&1; then
    launchctl bootout "$DOMAIN/$LABEL"
  fi
}

if [[ "${1:-}" == "--uninstall" ]]; then
  unload_if_loaded
  rm -f "$PLIST"
  echo "Removed $LABEL. Logs kept at $LOG_FILE"
  exit 0
fi

HOUR="${1:-5}"
MINUTE="${2:-0}"

MISE="$(command -v mise || true)"
if [[ -z "$MISE" ]]; then
  echo "error: mise not found on PATH — install it first (the agent runs 'mise run scrape')" >&2
  exit 1
fi

mkdir -p "$LOG_DIR" "$(dirname "$PLIST")"

cat > "$PLIST" <<PLIST_EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>$LABEL</string>
    <key>ProgramArguments</key>
    <array>
        <string>$MISE</string>
        <string>run</string>
        <string>scrape</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$REPO_ROOT</string>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>$HOUR</integer>
        <key>Minute</key>
        <integer>$MINUTE</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>$LOG_FILE</string>
    <key>StandardErrorPath</key>
    <string>$LOG_FILE</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
PLIST_EOF

unload_if_loaded
launchctl bootstrap "$DOMAIN" "$PLIST"

printf 'Installed %s — runs daily at %02d:%02d\n' "$LABEL" "$HOUR" "$MINUTE"
echo "  repo : $REPO_ROOT"
echo "  logs : $LOG_FILE"
echo
echo "Run it now to check it works:  launchctl kickstart -p $DOMAIN/$LABEL"
echo "Remove it:                     ./ops/install-scrape-agent.sh --uninstall"
