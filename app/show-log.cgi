#!/usr/bin/env bash

echo "Content-type: text/html"; echo

cat <<EOF
<!DOCTYPE html>
<head>
  <title>Storage Analyzer</title>
  <meta charset="utf-8" />
  <link rel="stylesheet" type="text/css" href="style.css">
</head>
 <body>
EOF

cat header.htm | sed 's/>Snapshot</>Log of last scan</'

echo -n "<div class=\"log-display\">"
LOG="$(bash log.cgi | sed 's#Content-type: text/plain##' | sed '/^$/{:a;N;s/\n$//;ta}' | sed 's/\x1b\[[0-9;]*[a-zA-Z]//g')"
echo "$LOG"
echo "</div>"

cat footer.htm

cat <<EOF
  </body>
</html>
EOF