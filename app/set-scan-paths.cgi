#!/usr/bin/env bash

set -euo pipefail

LOG_FILE="${DUC_LOG_FILE:-/var/log/duc.log}"
PERSISTED_SCAN_PATHS_FILE=/config/scan_paths
SCAN_ROOT=/scan

echo "Content-type: application/json"
echo ""

# Read the raw POST data
read -r -d '' POST_DATA || true

# Function to safely create a JSON string
json_escape() {
  local json_string
  json_string=$(jq -Rs . <<<"$1" | jq -r '.[0:length-1]')
  echo -n "${json_string}"
}

# Check if we have JSON input
if [[ "$POST_DATA" =~ ^\{.*\}$ ]]; then
  # Parse JSON input
  if ! paths_json=$(jq -r '.paths[]' <<<"$POST_DATA" 2>/dev/null); then
    echo '{"success": false, "error": "Invalid JSON input"}'
    exit 0
  fi
  
  # Read paths from JSON array
  mapfile -t parts <<< "$paths_json"
else
  # Fallback to old form-encoded format for backward compatibility
  val=$(echo "$POST_DATA" | sed -n 's/.*\bpaths=\([^&]*\).*/\1/p' | head -n 1)
  paths_raw=$(echo "$val" | tr -d '\r\n' | jq -sRr @uri | sed 's/%2F/\//g; s/%2C/,/g')
  
  if [[ -z "$paths_raw" ]]; then
    echo '{"success": false, "error": "No paths provided"}'
    exit 0
  fi
  
  # Split by comma, handling quoted strings if present
  IFS=',' read -r -a parts <<< "$paths_raw"
fi

mkdir -p /config

out=""
count=0
for p in "${parts[@]}"; do
  # Trim whitespace and handle empty paths
  p=$(echo "$p" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')
  [[ -z "$p" ]] && continue
  
  # Handle root path
  if [[ "$p" == "/" ]]; then
    p="$SCAN_ROOT"
  else
    # Remove any leading /scan prefix if present
    p=$(echo "$p" | sed 's|^/\?scan/\?|/|' | sed 's|^/|/scan/|')
    p="${p%/}"  # Remove trailing slash if present
  fi
  
  # Validate the path is under SCAN_ROOT
  if [[ "$p" != "$SCAN_ROOT"* ]]; then
    error_msg=$(echo "Invalid path (must be under /scan): $p" | jq -sRr @json)
    echo "{\"success\": false, \"error\": $error_msg}"
    exit 0
  fi

  # Basic path traversal check
  if [[ "$p" == *".."* ]]; then
    error_msg=$(echo "Invalid path (contains '..'): $p" | jq -sRr @json)
    echo "{\"success\": false, \"error\": $error_msg}"
    exit 0
  fi

  # Check if path exists and is a directory
  if [[ ! -d "$p" ]]; then
    error_msg=$(echo "Path does not exist or is not a directory: $p" | jq -sRr @json)
    echo "{\"success\": false, \"error\": $error_msg}"
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
