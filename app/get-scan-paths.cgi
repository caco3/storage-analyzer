#!/usr/bin/env bash

set -euo pipefail

PERSISTED_SCAN_PATHS_FILE=/config/scan_paths

echo "Content-type: application/json"
echo ""

mkdir -p /config

paths=""
if [[ -f "$PERSISTED_SCAN_PATHS_FILE" ]]; then
  paths=$(cat "$PERSISTED_SCAN_PATHS_FILE" 2>/dev/null | tr -d '\r' || true)
fi

if [[ -z "$paths" ]]; then
  paths="/scan"
fi

first=true
printf '{"success": true, "paths": ['
while IFS= read -r line; do
  line=$(echo "$line" | tr -d '\r\n')
  [[ -z "$line" ]] && continue
  if [[ "$first" == true ]]; then
    first=false
  else
    printf ','
  fi
  printf '"%s"' "$line"
done <<<"$paths"
printf ']}'
