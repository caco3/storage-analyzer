#!/usr/bin/env bash

set -euo pipefail

# Source environment variables
source "/env.sh"

echo "Content-type: application/json"
echo ""

exclude=""
if [[ -f "$EXCLUDE_FILE" ]]; then
  exclude=$(cat "$EXCLUDE_FILE" 2>/dev/null | tr -d '\r\n' || true)
else
  exclude="$DEFAULT_EXCLUDE"
fi

echo "{\"success\": true, \"exclude\": \"$exclude\"}"
