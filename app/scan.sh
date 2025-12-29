#!/usr/bin/env bash

set -euo pipefail

DATABASE="/database/duc_"`date +"%Y-%m-%d_%H-%M-%S".db`

LOG_FILE="${DUC_LOG_FILE:-/var/log/duc.log}"
LOCK_DIR="/tmp/scan.lock"

echo "Excluding files/folders with the following patterns: $EXCLUDE"
EXCLUDE=`echo $EXCLUDE | sed "s/,/ /g"`
EXCLUDE=( `for a in ${EXCLUDE[@]}; do echo -n "--exclude $a "; done` )

# Acquire lock atomically using mkdir (portable). If it exists, just exit silently.
if mkdir "$LOCK_DIR" 2>/dev/null; then
    trap 'rm -rf "$LOCK_DIR"' EXIT

    {
        echo "Start of scan: $(date) (Database: $DATABASE)"
        /usr/local/bin/duc index --progress /scan -d $DATABASE --check-hard-links ${EXCLUDE[@]}
        # --exclude=Selektion --exclude=Speziell --exclude=roms
        status=$?
        echo "End of scan: $(date) (exit code: $status)"

        # Data Size
        # 2025-12-29 08:06:01 2785165  343721 390117691392 /scan
        DATA_SIZE=`/usr/local/bin/duc info -d $DATABASE -b | tail -n 1 | awk '{print $5}'`
        echo "Data size: $((DATA_SIZE / 1024 / 1024)) MB ($DATA_SIZE bytes)"
        # Rename database to include data size
        NEW_DATABASE="${DATABASE%.db}_${DATA_SIZE}.db"
        mv "$DATABASE" "$NEW_DATABASE"
        DATABASE="$NEW_DATABASE"

        # Compress database
        echo "Compressing database: $DATABASE..."
        zstd -19 -f "$DATABASE" -o "$DATABASE.zst"
        echo "Compressed database: $DATABASE.zst"
        echo "Database size: "$(du -h "$DATABASE" | cut -f1)" (compressed: "$(du -h "$DATABASE.zst" | cut -f1) ")"
        rm "$DATABASE"
        # Propagate exit status of duc from this subshell to pipeline.
        exit $status
    } 2>&1 | tee -a "$LOG_FILE"

    # Retrieve exit status of the block (first element) from PIPESTATUS.
    scan_status=${PIPESTATUS[0]}
    exit $scan_status
fi
