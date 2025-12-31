#!/usr/bin/env bash

# Handle content-only request first
if [[ "${QUERY_STRING}" == "content=only" ]]; then
    echo "Content-type: text/plain"; echo
    LOG="$(bash log.cgi | sed 's#Content-type: text/plain##' | sed '/^$/{:a;N;s/\n$//;ta}' | sed 's/\x1b\[[0-9;]*[a-zA-Z]//g')"
    echo "$LOG"
    exit 0
fi

echo "Content-type: text/html"; echo

cat <<EOF
<!DOCTYPE html>
<head>
  <title>Storage Analyzer</title>
  <meta charset="utf-8" />
  <link rel="stylesheet" type="text/css" href="style.css">
  <script>
    // Auto-reload log content every second
    function reloadLog() {
      fetch('show-log.cgi?content=only')
        .then(response => response.text())
        .then(data => {
          document.getElementById('log-display').innerHTML = data;
        })
        .catch(error => console.error('Error reloading log:', error));
    }
    
    // Start auto-reload
    setInterval(reloadLog, 1000);
  </script>
</head>
 <body>
EOF

cat header.htm | sed 's/>Snapshot</>Log</'

echo -n "<div id=\"log-display\" class=\"log-display\">"
LOG="$(bash log.cgi | sed 's#Content-type: text/plain##' | sed '/^$/{:a;N;s/\n$//;ta}' | sed 's/\x1b\[[0-9;]*[a-zA-Z]//g')"
echo "$LOG"
echo "</div>"

cat footer.htm

cat <<EOF
  </body>
</html>
EOF