#!/usr/bin/env bash

set -euo pipefail

PERSISTED_EXCLUDE_FILE=/config/exclude

echo "Content-type: application/json"
echo ""

mkdir -p /config

exclude="proc sys dev cdrom run usr"
if [[ -f "$PERSISTED_EXCLUDE_FILE" ]]; then
  exclude=$(cat "$PERSISTED_EXCLUDE_FILE" 2>/dev/null | tr -d '\r\n' || true)
else
  exclude="${EXCLUDE:-}"
fi

echo "{\"success\": true, \"exclude\": \"$exclude\"}"
