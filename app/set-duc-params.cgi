#!/usr/bin/env bash

set -euo pipefail

# Source environment variables
source "$(dirname "$0")/env.sh"

echo "Content-type: application/json"
echo ""

# Read POST data
read -r POST_DATA || true

# Parse POST data
CHECK_HARD_LINKS=$(echo "$POST_DATA" | sed -n 's/.*check_hard_links=\([^&]*\).*/\1/p' | sed 's/%20/ /g' | sed 's/+//g')
MAX_DEPTH=$(echo "$POST_DATA" | sed -n 's/.*max_depth=\([^&]*\).*/\1/p' | sed 's/%20/ /g' | sed 's/+//g')

case "$CHECK_HARD_LINKS" in
    yes|no) ;;
    *) echo '{"success": false, "error": "Invalid check_hard_links value"}'; exit 1 ;;
esac

case "$MAX_DEPTH" in
    [1-9]|10) ;;
    *) echo '{"success": false, "error": "Invalid max_depth value"}'; exit 1 ;;
esac

# Save to config file
cat > "$DUC_PARAMS_FILE" << EOF
CHECK_HARD_LINKS=$CHECK_HARD_LINKS
MAX_DEPTH=$MAX_DEPTH
EOF

# Log the change
echo "$(date): parameters updated: check-hard-links=$CHECK_HARD_LINKS, max-depth=$MAX_DEPTH" >> "$LOG_FILE"

# Output JSON response
cat << EOF
{
  "success": true,
  "check_hard_links": "$CHECK_HARD_LINKS",
  "max_depth": "$MAX_DEPTH"
}
EOF
