#!/usr/bin/env bash

set -euo pipefail

# Source environment variables
source "/env.sh"

echo "Content-type: application/json"
echo ""

# Read POST data
read -r POST_DATA || true

# Extract db parameter (URL encoded)
SNAPSHOT_PATH=$(echo "$POST_DATA" | sed 's/.*db=\([^&]*\).*/\1/' | sed 's/%2F/\//g' | sed 's/+/ /g')

# Validate the path
if [[ -z "$SNAPSHOT_PATH" ]]; then
    echo '{"success": false, "error": "No snapshot specified"}'
    exit 0
fi

# Security: ensure path is within SNAPSHOTS_FOLDER and is a .db file
if [[ "$SNAPSHOT_PATH" != "$SNAPSHOTS_FOLDER/duc_"* ]] || [[ "$SNAPSHOT_PATH" != *".db" ]]; then
    echo '{"success": false, "error": "Invalid snapshot path"}'
    exit 0
fi

# The actual file is .db.zst (compressed)
ZST_FILE="${SNAPSHOT_PATH}.zst"

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
