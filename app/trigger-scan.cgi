#!/usr/bin/env bash

set -euo pipefail

# Source environment variables
source "/env.sh"

echo "Content-type: application/json"
echo ""

if [ -d "$LOCK_DIR" ]; then
    message="A scan is already in progress"
    response="{\"success\": false, \"message\": \"$message\"}"
elif [ -d "$REQUEST_DIR" ]; then
    message="A scan has already been requested"
    response="{\"success\": false, \"message\": \"$message\"}"
else
    mkdir -p "$REQUEST_DIR"
    # clear logfile
    echo "" > "$LOG_FILE"
    message="Scan will start within one minute"
    response="{\"success\": true, \"message\": \"$message\"}"
fi

echo "$(date): $message" >> $LOG_FILE # append the message to the log file
echo $response # UI response
