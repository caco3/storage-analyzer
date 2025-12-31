#!/usr/bin/env bash

set -euo pipefail

# Source environment variables
source "/env.sh"

echo "Content-type: text/plain"; echo
cat "$LOG_FILE"
