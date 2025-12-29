#!/usr/bin/env bash

set -euo pipefail

LOCK_DIR="/tmp/scan.lock"
REQUEST_DIR="/tmp/scan_requested"

echo "Content-type: application/json"
echo ""

if [ -d "$LOCK_DIR" ]; then
    echo '{"success": false, "message": "A scan is already in progress"}'
elif [ -d "$REQUEST_DIR" ]; then
    echo '{"success": false, "message": "A scan has already been requested"}'
else
    mkdir -p "$REQUEST_DIR"
    echo '{"success": true, "message": "Scan will start within one minute"}'
fi
