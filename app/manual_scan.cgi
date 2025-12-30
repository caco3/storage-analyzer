#!/usr/bin/env bash

set -euo pipefail

LOG_FILE="${DUC_LOG_FILE:-/var/log/duc.log}"
LOCK_DIR="/tmp/scan.lock"
REQUEST_DIR="/tmp/scan_requested"

echo "Content-type: text/html"; echo

cat <<EOF
<!DOCTYPE html>
<head>
  <title>Storage Analyzer</title>
  <meta charset="utf-8" />
  <link rel="stylesheet" type="text/css" href="style.css">
</head>
 <body>
EOF

cat header.htm | sed 's/>Snapshot</>Manual Scan</'

if [ -d "$LOCK_DIR" ]; then
    echo "A scan is already in progress:"; echo
    echo -n "<div class=\"log-display\">"
    cat "$LOG_FILE"
    echo "</div>"
elif [ -d "$REQUEST_DIR" ]; then
    echo "A manual scan has already been requested and will start within one minute."
else
    mkdir -p "$REQUEST_DIR"
    echo "A scan will be started within one minute."
fi
