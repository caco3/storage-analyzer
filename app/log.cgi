#!/usr/bin/env bash

set -euo pipefail

# Source environment variables
source "$(dirname "$0")/env.sh"

echo "Content-type: text/plain"; echo
cat "$LOG_FILE"
