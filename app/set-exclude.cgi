#!/usr/bin/env bash

set -euo pipefail

# Source environment variables
source "/env.sh"

echo "Content-type: application/json"
echo ""

read -r POST_DATA || true

urldecode() {
  # Proper URL decode that handles all percent-encoded characters
  local encoded="$1"
  local decoded=""
  local i=0
  local len=${#encoded}
  
  while [ $i -lt $len ]; do
    local c="${encoded:$i:1}"
    case "$c" in
      +) decoded+=" "; i=$((i+1)) ;;
      %)
        if [ $((i+2)) -lt $len ]; then
          local hex="${encoded:$((i+1)):2}"
          if [[ "$hex" =~ ^[0-9A-Fa-f]{2}$ ]]; then
            decoded+="\\x$hex"
            i=$((i+3))
          else
            decoded+="$c"
            i=$((i+1))
          fi
        else
          decoded+="$c"
          i=$((i+1))
        fi
        ;;
      *)
        decoded+="$c"
        i=$((i+1))
        ;;
    esac
  done
  
  echo -e "$decoded"
}

val=$(echo "$POST_DATA" | sed -n 's/.*\bexclude=\([^&]*\).*/\1/p' | head -n 1)
exclude=$(urldecode "$val")
exclude=$(echo "$exclude" | tr -d '\r\n')

echo "$exclude" > "$EXCLUDE_FILE" 2>/dev/null || true

echo "$(date) Updated exclude patterns to: $exclude" >> "$LOG_FILE" 2>/dev/null || true

# JSON escape the exclude patterns for the response
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
echo "{\"success\": true, \"message\": \"Exclude patterns updated\", \"exclude\": \"$escaped_exclude\"}"
