#!/usr/bin/env bash

set -euo pipefail

LOCK_DIR="/tmp/scan.lock"
REQUEST_DIR="/tmp/scan_requested"
LOG_FILE="${DUC_LOG_FILE:-/var/log/duc.log}"

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


echo "$message" >> $LOG_FILE # append the message to the log file
echo $response # UI response
