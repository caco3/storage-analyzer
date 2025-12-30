#!/usr/bin/env bash

set -euo pipefail

LOG_FILE="${DUC_LOG_FILE:-/var/log/duc.log}"
PERSISTED_SCAN_PATHS_FILE=/config/scan_paths
SCAN_ROOT=/scan

echo "Content-type: application/json"
echo ""

read -r POST_DATA || true

urldecode() {
  echo "$1" \
    | sed 's/+/ /g' \
    | sed 's/%2F/\//g' \
    | sed 's/%2C/,/g'
}

val=$(echo "$POST_DATA" | sed -n 's/.*\bpaths=\([^&]*\).*/\1/p' | head -n 1)
paths_raw=$(urldecode "$val")
paths_raw=$(echo "$paths_raw" | tr -d '\r\n')

mkdir -p /config

if [[ -z "$paths_raw" ]]; then
  echo '{"success": false, "error": "No paths provided"}'
  exit 0
fi

# Accept comma-separated list of absolute paths under /scan
IFS=',' read -r -a parts <<<"$paths_raw"

out=""
count=0
for p in "${parts[@]}"; do
  p="/scan"$(echo "$p" | sed 's/^ *//; s/ *$//')
  [[ -z "$p" ]] && continue

  if [[ "$p" == "/scan" ]]; then
    :
  elif [[ "$p" != "$SCAN_ROOT/"* ]]; then
    echo '{"success": false, "error": "Invalid path (must be under /scan)"}'
    exit 0
  fi

  if [[ "$p" == *".."* ]]; then
    echo '{"success": false, "error": "Invalid path"}'
    exit 0
  fi

  if [[ ! -d "$p" ]]; then
    echo '{"success": false, "error": "Path does not exist"}'
    exit 0
  fi

  out+="$p"$'\n'
  count=$((count+1))
done

if [[ $count -eq 0 ]]; then
  echo '{"success": false, "error": "No valid paths selected"}'
  exit 0
fi

echo -n "$out" > "$PERSISTED_SCAN_PATHS_FILE" 2>/dev/null || true

echo "$(date) Updated scan paths: $paths_raw" >> "$LOG_FILE" 2>/dev/null || true

echo '{"success": true, "message": "Scan paths updated"}'
