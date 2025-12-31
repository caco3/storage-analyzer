#!/usr/bin/env bash

set -euo pipefail

# Source environment variables
source "/env.sh"

# Ensure directories exist
mkdir -p "$CONFIG_DIR"
mkdir -p "$SNAPSHOTS_FOLDER"
mkdir -p "$SNAPSHOTS_FOLDER_TEMP"

touch "$LOG_FILE"

if [[ -f "$SCHEDULE_FILE" ]]; then
	PERSISTED_SCHEDULE=$(cat "$SCHEDULE_FILE" | tr -d '\r\n')
	if [[ -n "${PERSISTED_SCHEDULE}" ]]; then
		echo "Using persisted schedule from $SCHEDULE_FILE: ${PERSISTED_SCHEDULE}" | tee -a "$LOG_FILE"
		SCHEDULE="${PERSISTED_SCHEDULE}"
	fi
fi

# Basic validation for SCHEDULE (5 fields). If invalid, fallback to midnight.
if ! echo "$SCHEDULE" | awk 'NF==5' >/dev/null 2>&1; then
	echo "Invalid SCHEDULE '$SCHEDULE' - falling back to '0 0 * * *'" | tee -a "$LOG_FILE"
	SCHEDULE="0 0 * * *"
fi

echo "Creating cron schedule: $SCHEDULE"
CRON_FILE=/etc/cron.d/duc-index
{
	echo "# Auto-generated Duc cron tasks"
	echo "# Manual scan request poller"
	echo "* * * * * root /manual_scan.sh"
	echo "# Scheduled full scan"
	echo "$SCHEDULE root /scan.sh"
} > "$CRON_FILE"
chmod 0644 "$CRON_FILE"
cron

echo "Launching webserver"
rm -f /var/run/fcgiwrap.socket
nohup fcgiwrap -s unix:/var/run/fcgiwrap.socket &
while ! [ -S /var/run/fcgiwrap.socket ]; do sleep .2; done
chmod 777 /var/run/fcgiwrap.socket
test -f nohup.out && rm -f ./nohup.out

# Cleanup: remove all uncompressed snapshots to save memory
rm -f "$SNAPSHOTS_FOLDER"/*.db 2>/dev/null || true

echo "You can access the service at http://localhost:80/ resp. at the exposed port"
nginx
