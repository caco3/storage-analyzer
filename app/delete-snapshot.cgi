#!/usr/bin/env bash

set -euo pipefail

DB_FOLDER="/snapshots"

echo "Content-type: application/json"
echo ""

# Read POST data
read -r POST_DATA || true

# Extract db parameter (URL encoded)
DB_PATH=$(echo "$POST_DATA" | sed 's/.*db=\([^&]*\).*/\1/' | sed 's/%2F/\//g' | sed 's/+/ /g')

# Validate the path
if [[ -z "$DB_PATH" ]]; then
    echo '{"success": false, "error": "No database specified"}'
    exit 0
fi

# Security: ensure path is within DB_FOLDER and is a .db file
if [[ "$DB_PATH" != "$DB_FOLDER/duc_"* ]] || [[ "$DB_PATH" != *".db" ]]; then
    echo '{"success": false, "error": "Invalid database path"}'
    exit 0
fi

# The actual file is .db.zst (compressed)
ZST_FILE="${DB_PATH}.zst"

if [[ ! -f "$ZST_FILE" ]]; then
    echo '{"success": false, "error": "Snapshot not found"}'
    exit 0
fi

# Delete the compressed file
if rm -f "$ZST_FILE"; then
    echo '{"success": true, "message": "Snapshot deleted"}'
else
    echo '{"success": false, "error": "Failed to delete snapshot"}'
fi
