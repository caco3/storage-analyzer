#!/usr/bin/env bash

echo "Content-type: application/json"
echo ""

CONFIG_FILE="./duc-params.conf"

# Initialize defaults
ONE_FILE_SYSTEM="no"
CHECK_HARD_LINKS="yes"
MAX_DEPTH="5"

# Load from config file if it exists
if [ -f "$CONFIG_FILE" ]; then
    ONE_FILE_SYSTEM=$(grep "^ONE_FILE_SYSTEM=" "$CONFIG_FILE" 2>/dev/null | cut -d'=' -f2 || echo "no")
    CHECK_HARD_LINKS=$(grep "^CHECK_HARD_LINKS=" "$CONFIG_FILE" 2>/dev/null | cut -d'=' -f2 || echo "yes")
    MAX_DEPTH=$(grep "^MAX_DEPTH=" "$CONFIG_FILE" 2>/dev/null | cut -d'=' -f2 || echo "5")
fi

# Set defaults if empty
ONE_FILE_SYSTEM=${ONE_FILE_SYSTEM:-"no"}
CHECK_HARD_LINKS=${CHECK_HARD_LINKS:-"yes"}
MAX_DEPTH=${MAX_DEPTH:-"5"}

# Output JSON response
cat << EOF
{
  "success": true,
  "one_file_system": "$ONE_FILE_SYSTEM",
  "check_hard_links": "$CHECK_HARD_LINKS",
  "max_depth": "$MAX_DEPTH"
}
EOF

# Log the current parameters (if log file is writable)
LOG_FILE="${DUC_LOG_FILE:-/var/log/duc.log}"
if [ -w "$(dirname "$LOG_FILE")" ] || [ -w "$LOG_FILE" ]; then
    echo "$(date): DUC parameters retrieved: one-file-system=$ONE_FILE_SYSTEM, check-hard-links=$CHECK_HARD_LINKS, max-depth=$MAX_DEPTH" >> "$LOG_FILE" 2>/dev/null || true
fi
