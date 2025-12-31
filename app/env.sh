#!/bin/bash

# Environment variables for storage-analyzer

# Directories
SNAPSHOTS_FOLDER="/snapshots"
SNAPSHOTS_FOLDER_TEMP="/snapshots/temp"
CONFIG_DIR="/config"

# Files
LOG_FILE="${DUC_LOG_FILE:-/var/log/duc.log}"
DUC_PARAMS_FILE="$CONFIG_DIR/duc-params"
EXCLUDE_FILE="$CONFIG_DIR/exclude"
SCHEDULE_FILE="$CONFIG_DIR/schedule"
CRON_FILE="/etc/cron.d/duc-index"

# Lock and request directories
LOCK_DIR="/tmp/scan.lock"
REQUEST_DIR="/tmp/scan_requested"

# Default values
DEFAULT_EXCLUDE="proc sys dev cdrom run usr"
DEFAULT_CHECK_HARD_LINKS="yes"
DEFAULT_MAX_DEPTH="5"
