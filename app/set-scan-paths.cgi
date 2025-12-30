#!/usr/bin/env bash

set -euo pipefail

LOG_FILE="${DUC_LOG_FILE:-/var/log/duc.log}"
PERSISTED_SCAN_PATHS_FILE=/config/scan_paths
SCAN_ROOT=/scan

echo "Content-type: application/json"
echo ""

# Debug: Log environment variables
# env > /tmp/cgi_env.log

# Read the raw POST data from stdin
if [ -z "$CONTENT_LENGTH" ] || [ "$CONTENT_LENGTH" -eq 0 ]; then
  echo '{"success": false, "error": "No data received"}'
  exit 0
fi

# Read exactly CONTENT_LENGTH bytes from stdin
POST_DATA=$(dd bs=1 count="$CONTENT_LENGTH" 2>/dev/null 2>/dev/null)

# Debug: Log the raw POST data
# echo "$POST_DATA" > /tmp/post_data.log

# Function to safely create a JSON string
json_escape() {
  local json_string
  json_string=$(jq -Rs . <<<"$1" | jq -r '.[0:length-1]')
  echo -n "${json_string}"
}

urldecode_path() {
  python3 -c 'import sys, urllib.parse; print(urllib.parse.unquote(sys.argv[1]))' "$1"
}

# Initialize array to store paths
declare -a parts=()

# Check if we have JSON input
if [[ "${CONTENT_TYPE:-}" == *"application/json"* ]]; then
  if ! mapfile -t parts < <(jq -r '.paths[]' <<<"$POST_DATA" 2>/dev/null); then
    echo '{"success": false, "error": "Invalid JSON input"}'
    exit 0
  fi
else
  # Fallback to old form-encoded format for backward compatibility
  val=$(echo "$POST_DATA" | sed -n 's/.*\bpaths=\([^&]*\).*/\1/p' | head -n 1)
  paths_raw=$(echo "$val" | tr -d '\r\n' | jq -sRr @uri | sed 's/%2F/\//g; s/%2C/,/g')

  if [ -n "$paths_raw" ]; then
    IFS=',' read -r -a parts <<< "$paths_raw"
  fi
fi

# If no paths found, return error
if [ ${#parts[@]} -eq 0 ]; then
  echo '{"success": false, "error": "No valid paths provided in request"}'
  exit 0
fi

mkdir -p /config

out=""
count=0
for p in "${parts[@]}"; do
  # Trim whitespace and handle empty paths
  p=$(echo "$p" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')
  [[ -z "$p" ]] && continue

  # Decode URL-encoding (supports unicode). We intentionally do NOT treat '+' as space.
  p=$(urldecode_path "$p")

  # Normalize client paths as scan-root-relative. Examples:
  # - "/"          -> "/scan"
  # - "/temp/x"    -> "/scan/temp/x"
  # - "temp/x"     -> "/scan/temp/x"
  # - "/scan/temp" -> "/scan/temp"
  if [[ "$p" == "/" || "$p" == "" ]]; then
    p="$SCAN_ROOT"
  else
    p="/$(echo "$p" | sed 's|^/\+||')"
    if [[ "$p" == "$SCAN_ROOT" || "$p" == "$SCAN_ROOT/"* ]]; then
      :
    else
      p="$SCAN_ROOT$p"
    fi
    p="${p%/}"
  fi

  # Basic path traversal check
  if [[ "$p" == *".."* ]]; then
    error_msg=$(jq -n --arg p "$p" '{error: "Invalid path (contains ..)", path: $p}' | jq -c .)
    echo "{\"success\": false, \"error\": $error_msg}"
    exit 0
  fi

  # Check if path exists and is a directory
  if [[ ! -d "$p" ]]; then
    error_msg=$(jq -n --arg p "$p" '{error: "Path does not exist or is not a directory", path: $p}' | jq -c .)
    echo "{\"success\": false, \"error\": $error_msg}"
    exit 0
  fi

  out+="$p"$'\n'
  count=$((count+1))
done

if [[ $count -eq 0 ]]; then
  error_msg=$(jq -n '{error: "No valid paths selected"}' | jq -c .)
  echo "{\"success\": false, \"error\": $error_msg}"
  exit 0
fi

echo -n "$out" > "$PERSISTED_SCAN_PATHS_FILE" 2>/dev/null || true

echo "$(date) Updated scan paths: ${parts[*]}" >> "$LOG_FILE" 2>/dev/null || true

echo '{"success": true, "message": "Scan paths updated"}'
