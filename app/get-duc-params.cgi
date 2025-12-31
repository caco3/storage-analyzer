#!/usr/bin/env bash

set -euo pipefail

# Source environment variables
source "/env.sh"

echo "Content-type: application/json"
echo ""

# Load from config file if it exists
if [ -f "$DUC_PARAMS_FILE" ]; then
    CHECK_HARD_LINKS=$(grep "^CHECK_HARD_LINKS=" "$DUC_PARAMS_FILE" 2>/dev/null | cut -d'=' -f2)
    MAX_DEPTH=$(grep "^MAX_DEPTH=" "$DUC_PARAMS_FILE" 2>/dev/null | cut -d'=' -f2)
fi

# Set defaults if empty
CHECK_HARD_LINKS=${CHECK_HARD_LINKS:-"$DEFAULT_CHECK_HARD_LINKS"}
MAX_DEPTH=${MAX_DEPTH:-"$DEFAULT_MAX_DEPTH"}

# Output JSON response
cat << EOF
{
  "success": true,
  "check_hard_links": "$CHECK_HARD_LINKS",
  "max_depth": "$MAX_DEPTH"
}
EOF

# Log the current parameters
LOG_FILE="${DUC_LOG_FILE:-/var/log/duc.log}"
echo "$(date): DUC parameters retrieved: check-hard-links=$CHECK_HARD_LINKS, max-depth=$MAX_DEPTH" >> "$LOG_FILE"
