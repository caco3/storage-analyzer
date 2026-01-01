#!/usr/bin/env bash
# Searches the /snapshots folders and retuns a list of all *.db files.
# For JSON simplicity (no coma after the last element, we simply add a 0 value at the end.

# Source environment variables
source "/env.sh"

echo "Content-type: application/json"
echo ""

echo "{"\"snapshots\"": ["
for f in `ls -c1 $SNAPSHOTS_FOLDER/duc_*.db.zst | sort`; do
    count=$(echo "$f" | tr -cd '_' | wc -c)
    if [ $count -eq 3 ]; then
        size=$(echo "$f" | cut -d'_' -f4)
        size=${size%.db.zst}
    else
        size=0
    fi
    f=${f%.zst}
    file_size=$(stat -c%s "$f.zst" 2>/dev/null || echo 0)
    echo "{\"name\": \"$f\", \"size\": $size, \"db-size\": $file_size},"
done
echo "null ]}"
