#!/usr/bin/env bash

# Source environment variables
source "/env.sh"

set -eo pipefail

get_db() {
    # Split the URL, extract "db" parameter and store its value in the $DB variable.
    # See https://stackoverflow.com/a/27671738/8369030.
    # If the "db" parameter can not be found or is empty, $DB gets set to "".
    URL=$1
    arr=(${URL//[?=&]/ })

    for i in {1..20}; do
        #echo "$i: ${arr[$i]}<br>"
        if [[ "${arr[$i]}" == "db" ]]; then
            let i=i+1
            DB=${arr[$i]}
            break;
        fi
    done
}

get_PATH_IN_SNAPSHOT() {
    # Split the URL, extract "path" parameter and store its value in the $PATH_IN_SNAPSHOT variable.
    # See https://stackoverflow.com/a/27671738/8369030.
    # If the "path" parameter can not be found or is empty, $PATH_IN_SNAPSHOT gets set to "".
    URL=$1
    arr=(${URL//[?=&]/ })

    for i in {1..20}; do
        #echo "$i: ${arr[$i]}<br>"
        if [[ "${arr[$i]}" == "path" ]]; then
            let i=i+1
            PATH_IN_SNAPSHOT=${arr[$i]}
            break;
        fi
    done
}


get_latest_db() {
    # Scans the snapshot folder and sets the variable $DB with the name of the latest snapshot (based on date/time in filename)
    WD=`pwd`
    for f in `ls -c1 $SNAPSHOTS_FOLDER/duc_*.db.zst | sort -r`; do
        DB="${f%.zst}"
        break
    done
    cd $WD
}


#echo "Content-type: text/html"; echo
#echo "URL: $REQUEST_URI<br>"

get_db "$REQUEST_URI"
if [[ "$DB" == "" ]]; then
    get_latest_db
    #echo "DB parameter is missing or empty, using latest DB: $DB!<br>"
fi
#echo "DB: $DB<br>"

if [[ "${DB:-}" == "" ]]; then
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
    cat header.htm | sed 's/>Snapshot</>No snapshots found</'
    cat <<EOF
      <div class="info-box">
        <h2>No snapshots available</h2>
        <p>No snapshot exists yet. Start a scan to create your first snapshot.</p>
        <p><a class="snapshot_link" href="manage-snapshots.cgi">Go to Manage</a></p>
      </div>
EOF
    cat footer.htm
    echo "</body></html>"
    exit 0
fi

# If the path variable is not set, no pie chart is shown
# In such case, redirect to the same URL but append "path=/scan"
get_PATH_IN_SNAPSHOT "$REQUEST_URI"
#echo "PATH: $PATH_IN_SNAPSHOT<br>"
if [[ "$PATH_IN_SNAPSHOT" == "" ]]; then
    #echo "path parameter is missing or empty!<br>"
    echo "Content-type: text/html"; echo
    echo "<meta http-equiv=refresh content=\"0; url=$REQUEST_URI?db=$DB&path=/scan\">"
    exit 0
fi

# Cleanup: remove all uncompressed snapshots to save memory
rm -f "$SNAPSHOTS_FOLDER"/*.db 2>/dev/null || true

# Decompress the selected snapshot
rm -f "$DB" 2>/dev/null || true
if [[ ! -f "$DB.zst" ]]; then
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
    cat header.htm | sed 's/>Snapshot</>Snapshot error</'
    cat <<EOF
      <div class="error_message">
        <h2 class="error">Snapshot file missing</h2>
        <p>Expected compressed snapshot: <code>$DB.zst</code></p>
      </div>
EOF
    cat footer.htm
    echo "</body></html>"
    exit 0
fi

zstd -d "$DB.zst" -o "$DB"

# Check if database format is supported
DB_ERROR=$(duc info --database="$DB" 2>&1 || true)
if echo "$DB_ERROR" | grep -q "unsupported DB type"; then
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
    cat header.htm | sed 's/>Snapshot</>Database error</'
    cat <<EOF
      <div class="error_message">
        <h2 class="error">Unsupported database format</h2>
        <p>The snapshot database was created with an older version of the storage-analyzer (v1.x.x using DUC v1.4.x) that uses a different database format.</p>
        <p>You have following options:</p>
        <ul>
          <li>&nbsp;&nbsp;- <a href="manage-snapshots.cgi">Delete all old snapshots</a> and start a new snapshot with the current version of the storage-analyzer</li>
          <li>&nbsp;&nbsp;- Migrate your old snapshots manually to the new format using the converter at <a href="https://github.com/caco3/duc-database-converter" target="_blank">https://github.com/caco3/duc-database-converter</a></li>
          <li>&nbsp;&nbsp;- Downgrade to a previous version of the storage-analyzer (v1.x.x) that supports DUC v1.4.x. Note that there will be no updates to that version.</li>
        </ul>
        <p><a href="duc.cgi">← Back to main page</a></p>
      </div>
EOF
    cat footer.htm
    echo "</body></html>"
    exit 0
# Another error occured
elif [ -n "$DB_ERROR" ]; then
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
    cat header.htm | sed 's/>Snapshot</>Database error</'
    cat <<EOF
      <div class="error_message">
        <h2 class="error">Database access error</h2>
        <p>Unable to access the snapshot database.</p>
        <p><strong>Error details:</strong> <code>$DB_ERROR</code></p>
        <p>You have following options:</p>
        <ul>
          <li>&nbsp;&nbsp;- <a href="manage-snapshots.cgi">Delete the corrupted snapshot</a> and create a new one</li>
        </ul>
        <p><a href="duc.cgi">← Back to main page</a></p>
      </div>
EOF
    cat footer.htm
    echo "</body></html>"
    exit 0
fi

exec duc cgi --database=$DB --dpi=120 --size=600 --list --levels 1 --gradient --header header.htm --footer footer.htm --css-url style.css --db-error db-error.cgi --path-error path-error.cgi
