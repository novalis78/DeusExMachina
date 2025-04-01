#!/bin/bash
# bash_config.sh - Central configuration for all Deus Ex Machina bash scripts

# Base directories
INSTALL_DIR="/opt/deus-ex-machina"
LOG_DIR="/var/log/deus-ex-machina"

# Heartbeat configuration
HEARTBEAT_INTERVAL=60  # seconds
LOG_FILE="$LOG_DIR/heartbeat.log"
JSON_OUT="$LOG_DIR/heartbeat.json"
PREV_JSON="$LOG_DIR/heartbeat_prev.json"
MAX_LOG_SIZE=10485760  # 10MB

# Breath configuration
BREATH_INTERVAL=1800  # 30 minutes
SCAN_PATHS=(
  "/etc/passwd"
  "/etc/ssh/sshd_config"
  "/etc/fstab"
  "/etc/crontab"
  "/etc/shadow"
  "/etc/hosts"
)
HASH_STORE="$LOG_DIR/breath_hashes.json"
TEMP_HASHES="/tmp/current_breath_hashes.json"
SERVICE_STATUS="$LOG_DIR/service_status.log"
CRON_SNAPSHOT="$LOG_DIR/cron_snapshot.txt"

# Vigilance configuration
MERKLE_BASE_DIR="/etc /usr/bin /usr/sbin /home"
MERKLE_STORE="$LOG_DIR/merkle_root.hash"
MERKLE_TEMP="/tmp/current_merkle.hash"
AUTH_LOG="/var/log/auth.log"
ALERT_LOG="$LOG_DIR/vigilance_alerts.log"

# Create log directory
mkdir -p "$LOG_DIR"