#!/usr/bin/env bash

set -euo pipefail


SNAPSHOTS_FOLDER="/snapshots"
SNAPSHOTS_FOLDER_TEMP="/snapshots/temp"
SNAPSHOT_FILE="duc_"`date +"%Y-%m-%d_%H-%M-%S".db`



LOG_FILE="${DUC_LOG_FILE:-/var/log/duc.log}"
LOCK_DIR="/tmp/scan.lock"

mkdir -p /config

SCAN_PATHS=("/scan")

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
        mkdir -p $SNAPSHOTS_FOLDER
        mkdir -p $SNAPSHOTS_FOLDER_TEMP
        echo "" > $LOG_FILE # clear the log file
        echo "Start of scan: $(date) (Snapshot: $SNAPSHOT_FILE)"
        echo "Scan roots: ${SCAN_PATHS[*]}"
        echo "Relevant DUC index parameters:"
        echo "  Paths: ${SCAN_PATHS[*]}"
        echo "  Database: -d $SNAPSHOTS_FOLDER_TEMP/$SNAPSHOT_FILE"
        echo "  Exclude patterns: ${EXCLUDE[@]}"
        echo "Full command: /usr/local/bin/duc index --progress ${SCAN_PATHS[*]} -d $SNAPSHOTS_FOLDER_TEMP/$SNAPSHOT_FILE --check-hard-links ${EXCLUDE[@]}"
        /usr/local/bin/duc index --progress "${SCAN_PATHS[@]}" -d $SNAPSHOTS_FOLDER_TEMP/$SNAPSHOT_FILE --check-hard-links ${EXCLUDE[@]}
        # --exclude=Selektion --exclude=Speziell --exclude=roms
        status=$?
        echo "End of scan: $(date) (exit code: $status)"

        # Data Size
        # 2025-12-29 08:06:01 2785165  343721 390117691392 /scan
        DATA_SIZE=`/usr/local/bin/duc info -d $SNAPSHOTS_FOLDER_TEMP/$SNAPSHOT_FILE -b | tail -n 1 | awk '{print $5}'`
        echo "Data size: $((DATA_SIZE / 1024 / 1024)) MB ($DATA_SIZE bytes)"
        # Rename snapshot to include data size
        NEW_SNAPSHOT_FILE="${SNAPSHOT_FILE%.db}_${DATA_SIZE}.db"
        mv "$SNAPSHOTS_FOLDER_TEMP/$SNAPSHOT_FILE" "$SNAPSHOTS_FOLDER_TEMP/$NEW_SNAPSHOT_FILE"
        SNAPSHOT_FILE="$NEW_SNAPSHOT_FILE"

        # Compress snapshot
        echo "Compressing snapshot: $SNAPSHOT_FILE..."
        zstd -19 -f "$SNAPSHOTS_FOLDER_TEMP/$SNAPSHOT_FILE" -o "$SNAPSHOTS_FOLDER/$SNAPSHOT_FILE.zst"
        echo "Snapshot size: "$(du -h "$SNAPSHOTS_FOLDER_TEMP/$SNAPSHOT_FILE" | cut -f1)" (compressed: "$(du -h "$SNAPSHOTS_FOLDER/$SNAPSHOT_FILE.zst" | cut -f1) ")"
        # remove uncompressed snapshot, its not needed anymore
        rm "$SNAPSHOTS_FOLDER_TEMP/$SNAPSHOT_FILE"
        # Cleanup: remove all uncompressed snapshots to save memory
        rm -f "$SNAPSHOTS_FOLDER"/*.db 2>/dev/null || true
        # Propagate exit status of duc from this subshell to pipeline.
        exit $status
    } 2>&1 | tee -a "$LOG_FILE"

    # Retrieve exit status of the block (first element) from PIPESTATUS.
    scan_status=${PIPESTATUS[0]}
    exit $scan_status
fi
