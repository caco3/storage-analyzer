#!/usr/bin/env bash

# Handle content-only request first
if [[ "${QUERY_STRING}" == "content=only" ]]; then
    echo "Content-type: text/plain"; echo
    LOG_CONTENT="$(bash log.cgi | sed 's#Content-type: text/plain##' | sed '/^$/{:a;N;s/\n$//;ta}' | sed 's/\x1b\[[0-9;]*[a-zA-Z]//g')"
    # Filter out progress lines for content-only request
    MAIN_LOG="$(echo "$LOG_CONTENT" | grep -v '] Indexed')"
    echo "$MAIN_LOG"
    exit 0
fi

echo "Content-type: text/html"; echo

cat <<EOF
<!DOCTYPE html>
<head>
  <title>Storage Analyzer</title>
  <meta charset="utf-8" />
  <link rel="stylesheet" type="text/css" href="style.css">
  <script src="jquery.min.js"></script>
  <script src="script.js"></script>
</head>
 <body>
EOF

cat header.htm | sed 's/>Snapshot</>Log</'

# Get the log content
LOG_CONTENT="$(bash log.cgi | sed 's#Content-type: text/plain##' | sed '/^$/{:a;N;s/\n$//;ta}' | sed 's/\x1b\[[0-9;]*[a-zA-Z]//g')"

# Extract progress lines (lines containing % progress)
PROGRESS_LINES="$(echo "$LOG_CONTENT" | grep '] Indexed')"
# Get only the latest progress line and clean it up
LATEST_PROGRESS="$(echo "$PROGRESS_LINES" | tail -1 | sed 's/.*] Indexed/Indexed/' | sed 's/skipping.*//')"

# Check if scan has completed
SCAN_COMPLETED="$(echo "$LOG_CONTENT" | grep "End of scan" | tail -1)"

# Filter out all progress lines from main log
MAIN_LOG="$(echo "$LOG_CONTENT" | grep -v '] Indexed')"

# Display progress frame (always shown)
echo "<div id=\"progress-display\" class=\"progress-display\">"
echo "<h3>Current Progress</h3>"
if [[ -n "$LATEST_PROGRESS" ]]; then
    if [[ -n "$SCAN_COMPLETED" ]]; then
        echo "<div class=\"progress-line progress-completed\">Scan completed - $LATEST_PROGRESS</div>"
    else
        echo "<div class=\"progress-line progress-ongoing\">Ongoing - $LATEST_PROGRESS</div>"
    fi
elif [[ -n "$SCAN_COMPLETED" ]]; then
    echo "<div class=\"progress-line progress-completed\">Scan completed</div>"
else
    echo "<div class=\"progress-line progress-idle\">No scan in progress</div>"
fi
echo "</div>"

echo -n "<div id=\"log-display\" class=\"log-display\">"
echo "$MAIN_LOG"
echo "</div>"

cat footer.htm

cat <<EOF
  </body>
</html>
EOF