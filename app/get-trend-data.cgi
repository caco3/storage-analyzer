#!/usr/bin/env bash

set -euo pipefail

# Source environment variables
source "/env.sh"

echo "Content-type: application/json"
echo ""

echo "{"
echo "\"snapshots\": ["

first=true
for f in `ls -c1 $SNAPSHOTS_FOLDER/duc_*.db.zst | sort`; do
    # Extract timestamp and size from filename
    filename=$(basename "$f" .db.zst)
    
    # Parse the filename: duc_YYYY-MM-DD_HH-MM-SS_SIZE
    if [[ $filename =~ ^duc_([0-9]{4})-([0-9]{2})-([0-9]{2})_([0-9]{2})-([0-9]{2})-([0-9]{2})_([0-9]+)$ ]]; then
        year="${BASH_REMATCH[1]}"
        month="${BASH_REMATCH[2]}"
        day="${BASH_REMATCH[3]}"
        hour="${BASH_REMATCH[4]}"
        minute="${BASH_REMATCH[5]}"
        second="${BASH_REMATCH[6]}"
        size="${BASH_REMATCH[7]}"
        
        # Format timestamp as ISO string
        timestamp="${year}-${month}-${day} ${hour}:${minute}:${second}"
        
        # Get file modification time for additional accuracy
        file_time=$(stat -c %Y "$f" 2>/dev/null || echo 0)
        
        # Skip zero-size snapshots
        if [ "$size" -gt 0 ]; then
            if [ "$first" = true ]; then
                first=false
            else
                echo ","
            fi
            echo "{"
            echo "  \"timestamp\": \"$timestamp\","
            echo "  \"date\": \"$year-$month-$day\","
            echo "  \"time\": \"$hour:$minute:$second\","
            echo "  \"size\": $size,"
            echo "  \"file_time\": $file_time,"
            echo "  \"filename\": \"$filename\""
            echo -n "}"
        fi
    fi
done

echo ""
echo "]"
echo "}"
