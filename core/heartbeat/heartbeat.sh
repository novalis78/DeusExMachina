#!/bin/bash
# heartbeat.sh - Lightweight liveness and health checks for core system metrics
# Part of the Deus Ex Machina project

# Configuration
INTERVAL=60   # seconds between checks
LOG_DIR="/var/log/deus-ex-machina"
LOG_FILE="$LOG_DIR/heartbeat.log"
JSON_OUT="$LOG_DIR/heartbeat.json"
PREV_JSON="$LOG_DIR/heartbeat_prev.json"

mkdir -p "$LOG_DIR"

# Function: log current timestamp
log_time() {
  date '+%Y-%m-%d %H:%M:%S'
}

# Function: system snapshot
capture_snapshot() {
  TIMESTAMP=$(log_time)

  CPU_LOAD=$(uptime | awk -F'load average:' '{ print $2 }' | cut -d',' -f1 | xargs)
  MEM_FREE=$(free -m | awk '/^Mem:/ { print $4 }')
  DISK_USAGE=$(df -h / | awk 'NR==2 { print $5 }')
  TOP_PROCESSES=$(ps -eo pid,ppid,cmd,%mem,%cpu --sort=-%cpu | head -n 6)
  OPEN_PORTS=$(ss -tuln | grep -v State | wc -l)

  cat <<EOF > "$JSON_OUT"
{
  "timestamp": "$TIMESTAMP",
  "cpu_load": "$CPU_LOAD",
  "memory_free_mb": "$MEM_FREE",
  "disk_usage_root": "$DISK_USAGE",
  "open_ports": $OPEN_PORTS
}
EOF

  echo "$TIMESTAMP | Heartbeat: CPU=$CPU_LOAD MEM=${MEM_FREE}MB DISK=$DISK_USAGE PORTS=$OPEN_PORTS" >> "$LOG_FILE"

  # Delta Tracking
  if [ -f "$PREV_JSON" ]; then
    echo "$TIMESTAMP | Δ heartbeat diff:" >> "$LOG_FILE"
    diff "$PREV_JSON" "$JSON_OUT" | grep "^[<>]" >> "$LOG_FILE"
  fi

  cp "$JSON_OUT" "$PREV_JSON"
}

# Main loop
while true; do
  capture_snapshot
  sleep "$INTERVAL"
done
