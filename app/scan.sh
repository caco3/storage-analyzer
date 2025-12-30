#!/usr/bin/env bash

set -euo pipefail


DATABASE_FOLDER="/database"
DATABASE_FOLDER_TEMP="/database/temp"
DATABASE_FILE="duc_"`date +"%Y-%m-%d_%H-%M-%S".db`



LOG_FILE="${DUC_LOG_FILE:-/var/log/duc.log}"
LOCK_DIR="/tmp/scan.lock"

mkdir -p /config

EXCLUDE_RAW=""
if [[ -f /config/exclude ]]; then
    EXCLUDE_RAW=$(cat /config/exclude 2>/dev/null | tr -d '\r\n' || true)
else
    EXCLUDE_RAW="${EXCLUDE:-}"
fi

echo "Excluding files/folders with the following patterns: ${EXCLUDE_RAW}"
EXCLUDE_RAW=$(echo "$EXCLUDE_RAW" | sed "s/,/ /g")
EXCLUDE=( $(for a in ${EXCLUDE_RAW}; do echo -n "--exclude $a "; done) )

# Acquire lock atomically using mkdir (portable). If it exists, just exit silently.
if mkdir "$LOCK_DIR" 2>/dev/null; then
    trap 'rm -rf "$LOCK_DIR"' EXIT

    {
        mkdir -p $DATABASE_FOLDER
        mkdir -p $DATABASE_FOLDER_TEMP
        echo "Start of scan: $(date) (Database: $DATABASE_FILE)"
        /usr/local/bin/duc index --progress /scan -d $DATABASE_FOLDER_TEMP/$DATABASE_FILE --check-hard-links ${EXCLUDE[@]}
        # --exclude=Selektion --exclude=Speziell --exclude=roms
        status=$?
        echo "End of scan: $(date) (exit code: $status)"

        # Data Size
        # 2025-12-29 08:06:01 2785165  343721 390117691392 /scan
        DATA_SIZE=`/usr/local/bin/duc info -d $DATABASE_FOLDER_TEMP/$DATABASE_FILE -b | tail -n 1 | awk '{print $5}'`
        echo "Data size: $((DATA_SIZE / 1024 / 1024)) MB ($DATA_SIZE bytes)"
        # Rename database to include data size
        NEW_DATABASE_FILE="${DATABASE_FILE%.db}_${DATA_SIZE}.db"
        mv "$DATABASE_FOLDER_TEMP/$DATABASE_FILE" "$DATABASE_FOLDER_TEMP/$NEW_DATABASE_FILE"
        DATABASE_FILE="$NEW_DATABASE_FILE"

        # Compress database
        echo "Compressing database: $DATABASE_FILE..."
        zstd -19 -f "$DATABASE_FOLDER_TEMP/$DATABASE_FILE" -o "$DATABASE_FOLDER/$DATABASE_FILE.zst"
        echo "Database size: "$(du -h "$DATABASE_FOLDER_TEMP/$DATABASE_FILE" | cut -f1)" (compressed: "$(du -h "$DATABASE_FOLDER/$DATABASE_FILE.zst" | cut -f1) ")"
        rm "$DATABASE_FOLDER_TEMP/$DATABASE_FILE"
        # Propagate exit status of duc from this subshell to pipeline.
        exit $status
    } 2>&1 | tee -a "$LOG_FILE"

    # Retrieve exit status of the block (first element) from PIPESTATUS.
    scan_status=${PIPESTATUS[0]}
    exit $scan_status
fi
