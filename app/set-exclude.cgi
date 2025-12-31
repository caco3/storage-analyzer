#!/usr/bin/env bash

set -euo pipefail

# Source environment variables
source "/env.sh"

echo "Content-type: application/json"
echo ""

read -r POST_DATA || true

urldecode() {
  echo "$1" \
    | sed 's/+/ /g' \
    | sed 's/%2A/*/g' \
    | sed 's/%2F/\//g' \
    | sed 's/%2C/,/g'
}

val=$(echo "$POST_DATA" | sed -n 's/.*\bexclude=\([^&]*\).*/\1/p' | head -n 1)
exclude=$(urldecode "$val")
exclude=$(echo "$exclude" | tr -d '\r\n')

echo "$exclude" > "$EXCLUDE_FILE" 2>/dev/null || true

echo "$(date) Updated exclude patterns to: $exclude" >> "$LOG_FILE" 2>/dev/null || true

echo "{\"success\": true, \"message\": \"Exclude patterns updated\", \"exclude\": \"$exclude\"}"
