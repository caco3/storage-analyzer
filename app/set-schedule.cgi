#!/usr/bin/env bash

set -euo pipefail

# Source environment variables
source "$(dirname "$0")/env.sh"

echo "Content-type: application/json"
echo ""

read -r POST_DATA || true

urldecode() {
  echo "$1" \
    | sed 's/+/ /g' \
    | sed 's/%2A/*/g' \
    | sed 's/%2F/\//g' \
    | sed 's/%2C/,/g'
}

extract_param() {
  local key="$1"
  local val
  val=$(echo "$POST_DATA" | sed -n "s/.*\b${key}=\([^&]*\).*/\1/p" | head -n 1)
  urldecode "$val"
}

mode=$(extract_param mode)
minute=$(extract_param minute)
hour=$(extract_param hour)
dow=$(extract_param dow)
dom=$(extract_param dom)

is_int() { [[ "$1" =~ ^[0-9]+$ ]]; }

validate_range() {
  local name="$1" val="$2" min="$3" max="$4"
  if ! is_int "$val"; then
    echo "{\"success\": false, \"error\": \"Invalid ${name}: not a number\"}"
    exit 0
  fi
  if (( val < min || val > max )); then
    echo "{\"success\": false, \"error\": \"Invalid ${name}: must be between ${min} and ${max}\"}"
    exit 0
  fi
}

if [[ -z "$mode" ]]; then
  echo '{"success": false, "error": "No mode provided"}'
  exit 0
fi

schedule=""
case "$mode" in
  hourly)
    validate_range "minute" "$minute" 0 59
    schedule="$minute * * * *"
    ;;
  daily)
    validate_range "minute" "$minute" 0 59
    validate_range "hour" "$hour" 0 23
    schedule="$minute $hour * * *"
    ;;
  weekly)
    validate_range "minute" "$minute" 0 59
    validate_range "hour" "$hour" 0 23
    validate_range "day of week" "$dow" 0 6
    schedule="$minute $hour * * $dow"
    ;;
  monthly)
    validate_range "minute" "$minute" 0 59
    validate_range "hour" "$hour" 0 23
    validate_range "day of month" "$dom" 1 31
    schedule="$minute $hour $dom * *"
    ;;
  *)
    echo '{"success": false, "error": "Unsupported mode"}'
    exit 0
    ;;
esac

echo "$schedule" > "$SCHEDULE_FILE" 2>/dev/null || true

{
  echo "# Auto-generated Duc cron tasks"
  echo "# Manual scan request poller"
  echo "* * * * * root /manual_scan.sh"
  echo "# Scheduled full scan"
  echo "$schedule root /scan.sh"
} > "$CRON_FILE"
chmod 0644 "$CRON_FILE"

echo "$(date) Updated schedule to: $schedule" >> "$LOG_FILE" 2>/dev/null || true

pid=$(pidof cron 2>/dev/null || true)
if [[ -n "$pid" ]]; then
  kill -HUP $pid 2>/dev/null || true
fi

echo "{\"success\": true, \"message\": \"Schedule updated\", \"schedule\": \"$schedule\"}"
