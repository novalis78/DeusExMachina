#!/bin/bash
# heartbeat.sh - Lightweight liveness and health checks for core system metrics
# Part of the Deus Ex Machina project

# Import configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Source bash configuration
if [ -f "$PROJECT_ROOT/scripts/bash_config.sh" ]; then
    source "$PROJECT_ROOT/scripts/bash_config.sh"
else
    # Default configuration if config file doesn't exist
    INTERVAL=60   # seconds between checks
    LOG_DIR="/var/log/deus-ex-machina"
    LOG_FILE="$LOG_DIR/heartbeat.log"
    JSON_OUT="$LOG_DIR/heartbeat.json"
    PREV_JSON="$LOG_DIR/heartbeat_prev.json"
    MAX_LOG_SIZE=10485760  # 10MB
fi

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Function: Log rotation
check_log_rotation() {
    if [ -f "$LOG_FILE" ] && [ $(stat -c%s "$LOG_FILE") -gt $MAX_LOG_SIZE ]; then
        mv "$LOG_FILE" "${LOG_FILE}.old"
        echo "$(date '+%Y-%m-%d %H:%M:%S') | Log rotated" > "$LOG_FILE"
    fi
}

# Function: log current timestamp
log_time() {
    date '+%Y-%m-%d %H:%M:%S'
}

# Function: safe command execution with timeout
safe_exec() {
    local cmd="$1"
    local default="$2"
    local timeout=5
    
    result=$(timeout $timeout bash -c "$cmd" 2>/dev/null || echo "$default")
    echo "$result"
}

# Function: system snapshot
capture_snapshot() {
    TIMESTAMP=$(log_time)
    
    # Safely get metrics with defaults and timeouts
    CPU_LOAD=$(safe_exec "uptime | awk -F'load average:' '{ print \$2 }' | cut -d',' -f1 | xargs" "0.00")
    MEM_FREE=$(safe_exec "free -m | awk '/^Mem:/ { print \$4 }'" "0")
    DISK_USAGE=$(safe_exec "df -h / | awk 'NR==2 { print \$5 }'" "0%")
    OPEN_PORTS=$(safe_exec "ss -tuln | grep -v State | wc -l" "0")
    UPTIME=$(safe_exec "uptime -p" "unknown")
    PROCESSES=$(safe_exec "ps -e | wc -l" "0")
    
    # Sanitize values for JSON
    DISK_USAGE=${DISK_USAGE//%/}
    
    # Generate JSON output
    cat <<EOF > "$JSON_OUT"
{
  "timestamp": "$TIMESTAMP",
  "cpu_load": "$CPU_LOAD",
  "memory_free_mb": "$MEM_FREE",
  "disk_usage_root": "$DISK_USAGE",
  "open_ports": $OPEN_PORTS,
  "uptime": "$UPTIME",
  "total_processes": $PROCESSES
}
EOF
    
    # Log summary
    echo "$TIMESTAMP | Heartbeat: CPU=$CPU_LOAD MEM=${MEM_FREE}MB DISK=$DISK_USAGE% PORTS=$OPEN_PORTS" >> "$LOG_FILE"
    
    # Delta Tracking with error handling
    if [ -f "$PREV_JSON" ]; then
        echo "$TIMESTAMP | Δ heartbeat diff:" >> "$LOG_FILE"
        diff "$PREV_JSON" "$JSON_OUT" | grep "^[<>]" >> "$LOG_FILE" 2>/dev/null || echo "No changes detected" >> "$LOG_FILE"
    fi
    
    # Save current state for next comparison
    cp "$JSON_OUT" "$PREV_JSON"
}

# Set up signal handling
trap 'echo "Heartbeat exiting on signal..."; exit 0' SIGINT SIGTERM

# Main loop with error handling
main() {
    echo "$(log_time) | Heartbeat starting..." >> "$LOG_FILE"
    
    while true; do
        check_log_rotation
        capture_snapshot
        sleep "$INTERVAL"
    done
}

main