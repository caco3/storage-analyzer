#!/usr/bin/env bash

set -euo pipefail

echo "Content-type: application/json"
echo ""

# Call the Python script to handle the logic
exec python3 "$(dirname "$0")/get-scan-paths.py"
