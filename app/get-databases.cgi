#!/usr/bin/env bash
# Searches the /databases folders and retuns a list of all *.db files.
# For JSON simplicity (no coma after the last element, we simply add a 0 value at the end.

DB_FOLDER="/database"

echo "Content-type: application/json"
echo ""

echo "{"\"databases\"": ["
for f in `ls -c1 $DB_FOLDER/duc_*.db.zst | sort`; do
    echo "{\"name\": \"${f%.zst}\", \"size\": $(stat -c%s "$f")}, "
done
echo "0 ]}"
