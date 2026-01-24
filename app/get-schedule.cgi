#!/usr/bin/env bash

set -euo pipefail

# Source environment variables
source "/env.sh"

echo "Content-type: application/json"
echo ""

schedule=""
supported=false
mode=""
minute="0"
hour="0"
dow="1"
dom="1"
raw_line=""

if [[ -f "$SCHEDULE_FILE" ]]; then
  schedule=$(cat "$SCHEDULE_FILE" 2>/dev/null | tr -d '\r\n' || true)
fi

if [[ -z "$schedule" ]] && [[ -f "$CRON_FILE" ]]; then
  raw_line=$(awk '$0 !~ /^#/ && NF>=7 && $6=="root" && $7 ~ /^\/scan\.sh/ {print; exit}' "$CRON_FILE" 2>/dev/null || true)
  raw_line=$(echo "$raw_line" | tr -d '\r\n')
  schedule=$(echo "$raw_line" | awk '{print $1" "$2" "$3" "$4" "$5}')
fi

# Check if schedule is disabled (no scan.sh entry in cron)
if [[ -z "$schedule" ]] || [[ "$schedule" == "disabled" ]]; then
  echo "{\"success\": true, \"supported\": true, \"mode\": \"disabled\", \"minute\": 0, \"hour\": 0, \"dow\": 0, \"dom\": 0, \"schedule\": \"disabled\"}"
  exit 0
fi

# Normalize any stray CRLF/newlines
schedule=$(echo "$schedule" | tr -d '\r\n')

# Split into fields without glob expansion ("*")
f1=""; f2=""; f3=""; f4=""; f5=""
IFS=' ' read -r f1 f2 f3 f4 f5 _rest <<<"$schedule"

if [[ "$f1" =~ ^[0-9]+$ ]] && [[ "$f2" == "*" ]] && [[ "$f3" == "*" ]] && [[ "$f4" == "*" ]] && [[ "$f5" == "*" ]]; then
  supported=true
  mode="hourly"
  minute="$f1"
elif [[ "$f1" =~ ^[0-9]+$ ]] && [[ "$f2" =~ ^[0-9]+$ ]] && [[ "$f3" == "*" ]] && [[ "$f4" == "*" ]] && [[ "$f5" == "*" ]]; then
  supported=true
  mode="daily"
  minute="$f1"
  hour="$f2"
elif [[ "$f1" =~ ^[0-9]+$ ]] && [[ "$f2" =~ ^[0-9]+$ ]] && [[ "$f3" == "*" ]] && [[ "$f4" == "*" ]] && [[ "$f5" =~ ^[0-6]$ ]]; then
  supported=true
  mode="weekly"
  minute="$f1"
  hour="$f2"
  dow="$f5"
elif [[ "$f1" =~ ^[0-9]+$ ]] && [[ "$f2" =~ ^[0-9]+$ ]] && [[ "$f3" =~ ^[0-9]+$ ]] && [[ "$f4" == "*" ]] && [[ "$f5" == "*" ]]; then
  supported=true
  mode="monthly"
  minute="$f1"
  hour="$f2"
  dom="$f3"
fi

echo "{\"success\": true, \"supported\": $supported, \"mode\": \"$mode\", \"minute\": $minute, \"hour\": $hour, \"dow\": $dow, \"dom\": $dom, \"schedule\": \"$schedule\"}"
