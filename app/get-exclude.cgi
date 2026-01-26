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

# JSON escape the exclude patterns
json_escape() {
  local str="$1"
  # Escape backslashes first, then quotes, then other special characters
  str="${str//\\/\\\\}"  # Escape backslashes
  str="${str//\"/\\\"}"  # Escape quotes
  str="${str//$'\n'/\\n}" # Escape newlines
  str="${str//$'\r'/\\r}" # Escape carriage returns
  str="${str//$'\t'/\\t}" # Escape tabs
  echo "$str"
}

escaped_exclude=$(json_escape "$exclude")
echo "{\"success\": true, \"exclude\": \"$escaped_exclude\"}"
