#!/usr/bin/env bash

set -euo pipefail

# Read POST data
read POST_DATA

echo "Content-type: application/json"
echo ""

# Validate inputs
case "$ONE_FILE_SYSTEM" in
    yes|no) ;;
    *) echo '{"success": false, "error": "Invalid one_file_system value"}'; exit 1 ;;
esac

case "$CHECK_HARD_LINKS" in
    yes|no) ;;
    *) echo '{"success": false, "error": "Invalid check_hard_links value"}'; exit 1 ;;
esac

case "$MAX_DEPTH" in
    [1-9]|10) ;;
    *) echo '{"success": false, "error": "Invalid max_depth value"}'; exit 1 ;;
esac

# Save to config file
CONFIG_FILE="/app/duc-params.conf"
cat > "$CONFIG_FILE" << EOF
ONE_FILE_SYSTEM=$ONE_FILE_SYSTEM
CHECK_HARD_LINKS=$CHECK_HARD_LINKS
MAX_DEPTH=$MAX_DEPTH
EOF

# Log the change
LOG_FILE="${DUC_LOG_FILE:-/var/log/duc.log}"
echo "$(date): parameters updated: one-file-system=$ONE_FILE_SYSTEM, check-hard-links=$CHECK_HARD_LINKS, max-depth=$MAX_DEPTH" >> "$LOG_FILE"

# Output JSON response
cat << EOF
{
  "success": true,
  "one_file_system": "$ONE_FILE_SYSTEM",
  "check_hard_links": "$CHECK_HARD_LINKS",
  "max_depth": "$MAX_DEPTH"
}
EOF
