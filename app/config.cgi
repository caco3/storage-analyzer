#!/usr/bin/env bash

set -euo pipefail

echo "Content-type: text/html"; echo

cat header.htm | sed 's/>Snapshot</>Configuration</'

cat config.htm

cat footer.htm
