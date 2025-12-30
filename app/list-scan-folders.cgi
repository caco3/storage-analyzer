#!/usr/bin/env bash

set -euo pipefail

SCAN_ROOT=/scan
MAX_DEPTH=3
MAX_FOLDERS=2000

EXCLUDE_FILE=/config/exclude
EXCLUDE_RAW=${EXCLUDE:-}

exclude_patterns=()

add_exclude_pattern() {
  local p=$1
  p=${p//$'\r'/}
  p=${p##[[:space:]]}
  p=${p%%[[:space:]]}
  [[ -z "$p" ]] && return 0
  [[ "$p" == \#* ]] && return 0
  p=${p#/}
  exclude_patterns+=("$p")
}

if [[ -f "$EXCLUDE_FILE" ]]; then
  while IFS= read -r line; do
    add_exclude_pattern "$line"
  done < "$EXCLUDE_FILE"
elif [[ -n "$EXCLUDE_RAW" ]]; then
  while IFS= read -r line; do
    add_exclude_pattern "$line"
  done <<<"$EXCLUDE_RAW"
fi

echo "Content-type: application/json"
echo ""

mkdir -p "$SCAN_ROOT"

first=true
count=0
printf '{"success": true, "folders": ['

find_args=("$SCAN_ROOT" -mindepth 1 -maxdepth "$MAX_DEPTH")
if (( ${#exclude_patterns[@]} > 0 )); then
  find_args+=(\( )
  for i in "${!exclude_patterns[@]}"; do
    p=${exclude_patterns[$i]}
    if (( i > 0 )); then
      find_args+=(-o)
    fi
    find_args+=(-path "*/$p" -o -path "*/$p/*")
  done
  find_args+=(\) -prune -o)
fi
find_args+=(-type d -print0)

while IFS= read -r -d '' d; do
  rel=${d#"$SCAN_ROOT"}
  [[ -z "$rel" ]] && continue
  count=$((count+1))
  if (( count > MAX_FOLDERS )); then
    break
  fi
  if [[ "$first" == true ]]; then
    first=false
  else
    printf ','
  fi
  depth=$(awk -F/ '{print NF-1}' <<<"$rel")
  printf '{"path":"%s","depth":%s}' "$rel" "$depth"
done < <(find "${find_args[@]}" 2>/dev/null | sort -z)

printf ']}'
