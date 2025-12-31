#!/usr/bin/env bash

# Read POST data (if any)
POST_DATA=""
if [ "$REQUEST_METHOD" = "POST" ]; then
    read -r POST_DATA
fi
# Parse POST data safely
if [ -n "$POST_DATA" ]; then
    ONE_FILE_SYSTEM=$(echo "$POST_DATA" | sed -n 's/.*one_file_system=\([^&]*\).*/\1/p' | sed 's/%20/ /g' | sed 's/+//g' | tr -d '\r\n')
    CHECK_HARD_LINKS=$(echo "$POST_DATA" | sed -n 's/.*check_hard_links=\([^&]*\).*/\1/p' | sed 's/%20/ /g' | sed 's/+//g' | tr -d '\r\n')
    MAX_DEPTH=$(echo "$POST_DATA" | sed -n 's/.*max_depth=\([^&]*\).*/\1/p' | sed 's/%20/ /g' | sed 's/+//g' | tr -d '\r\n')
fi

# Set defaults if parsing failed
ONE_FILE_SYSTEM=${ONE_FILE_SYSTEM:-"no"}
CHECK_HARD_LINKS=${CHECK_HARD_LINKS:-"yes"}
MAX_DEPTH=${MAX_DEPTH:-"5"}

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
CONFIG_FILE="./duc-params.conf"
cat > "$CONFIG_FILE" << EOF
ONE_FILE_SYSTEM=$ONE_FILE_SYSTEM
CHECK_HARD_LINKS=$CHECK_HARD_LINKS
MAX_DEPTH=$MAX_DEPTH
EOF

# Log the change (if log file is writable)
LOG_FILE="${DUC_LOG_FILE:-/var/log/duc.log}"
if [ -w "$(dirname "$LOG_FILE")" ] || [ -w "$LOG_FILE" ]; then
    echo "$(date): DUC parameters updated: one-file-system=$ONE_FILE_SYSTEM, check-hard-links=$CHECK_HARD_LINKS, max-depth=$MAX_DEPTH" >> "$LOG_FILE" 2>/dev/null || true
fi

# Output JSON response
cat << EOF
{
  "success": true,
  "one_file_system": "$ONE_FILE_SYSTEM",
  "check_hard_links": "$CHECK_HARD_LINKS",
  "max_depth": "$MAX_DEPTH"
}
EOF
