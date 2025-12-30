#!/usr/bin/env bash

set -euo pipefail

echo "Content-type: text/html"; echo

cat <<EOF
<!DOCTYPE html>
<head>
  <title>Storage Analyzer - Manage Snapshots</title>
  <meta charset="utf-8" />
  <link rel="stylesheet" type="text/css" href="style.css">
</head>
<body>
EOF

cat header.htm | sed 's/>Snapshot</>Manage Snapshots</'

cat manage-snapshots.html

cat footer.htm
echo "</body></html>"
