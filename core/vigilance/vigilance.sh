#!/bin/bash
# vigilance.sh - Deep anomaly detection and AI escalation trigger
# Part of the Deus Ex Machina project

# Import configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Source bash configuration
if [ -f "$PROJECT_ROOT/scripts/bash_config.sh" ]; then
    source "$PROJECT_ROOT/scripts/bash_config.sh"
else
    # Default configuration if config file doesn't exist
    MERKLE_BASE_DIR="/etc /usr/bin /usr/sbin /home"
    MERKLE_STORE="/var/log/deus-ex-machina/merkle_root.hash"
    MERKLE_TEMP="/tmp/current_merkle.hash"
    AUTH_LOG="/var/log/auth.log"
    ALERT_LOG="/var/log/deus-ex-machina/vigilance_alerts.log"
    LOG_DIR="/var/log/deus-ex-machina"
fi

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Set up logging
log_message() {
    local level="$1"
    local message="$2"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$level] [Vigilance] $message" >> "$LOG_DIR/vigilance.log"
    
    # Also log alerts to the alert log
    if [ "$level" = "ALERT" ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ALERT] $message" >> "$ALERT_LOG"
    fi
    
    echo "[Vigilance] $message"
}

# Function to generate a recursive hash of files (Merkle-ish) with resource limits
generate_merkle_hash() {
    log_message "INFO" "Generating Merkle-style hash..."
    
    # Use ionice to limit I/O impact and nice to reduce CPU priority
    ionice -c 3 nice -n 19 find $MERKLE_BASE_DIR -type f -not -path "*/\.*" -not -path "*/node_modules/*" \
        -not -path "*/venv/*" -exec sha256sum {} + 2>/dev/null | \
        sort | sha256sum | awk '{print $1}' > "$MERKLE_TEMP"
    
    if [ ! -s "$MERKLE_TEMP" ]; then
        log_message "ERROR" "Failed to generate Merkle hash"
        return 1
    fi
    
    log_message "INFO" "Merkle hash generated successfully"
    return 0
}

# Compare against previous Merkle root with proper error handling
check_integrity() {
    if [ ! -f "$MERKLE_TEMP" ]; then
        log_message "ERROR" "Merkle hash file not found"
        return 1
    }
    
    if [ ! -f "$MERKLE_STORE" ]; then
        cp "$MERKLE_TEMP" "$MERKLE_STORE"
        log_message "INFO" "Initial Merkle root stored."
        return 0
    fi

    if [ ! -r "$MERKLE_STORE" ] || [ ! -r "$MERKLE_TEMP" ]; then
        log_message "ERROR" "Cannot read Merkle hash files"
        return 1
    }

    old=$(cat "$MERKLE_STORE")
    new=$(cat "$MERKLE_TEMP")
    
    if [ -z "$old" ] || [ -z "$new" ]; then
        log_message "ERROR" "Empty Merkle hash detected"
        return 1
    }
    
    if [ "$old" != "$new" ]; then
        log_message "ALERT" "🔥 SYSTEM INTEGRITY ALERT: Merkle root mismatch!"
        log_message "INFO" "Old: $old"
        log_message "INFO" "New: $new"
        cp "$MERKLE_TEMP" "$MERKLE_STORE"
        return 2  # Return code 2 indicates integrity failure
    else
        log_message "INFO" "✅ Merkle root unchanged."
        return 0
    fi
}

# Analyze auth log for anomalies with proper error handling
scan_auth_logs() {
    log_message "INFO" "Scanning auth logs for suspicious entries..."
    
    if [ ! -f "$AUTH_LOG" ] || [ ! -r "$AUTH_LOG" ]; then
        log_message "WARNING" "Auth log not found or not readable: $AUTH_LOG"
        return 1
    fi
    
    # Search for suspicious patterns
    if suspicious=$(grep -Ei "failed|invalid|root|sudo|unauthorized|break-in" "$AUTH_LOG" | tail -n 20); then
        suspicious_count=$(echo "$suspicious" | wc -l)
        if [ "$suspicious_count" -gt 0 ]; then
            log_message "ALERT" "Found $suspicious_count suspicious auth log entries"
            echo "$suspicious" >> "$ALERT_LOG"
            return 2  # Return code 2 indicates suspicious activity
        else
            log_message "INFO" "No suspicious auth log entries found"
            return 0
        fi
    else
        log_message "INFO" "No suspicious auth log entries found"
        return 0
    fi
}

# Network anomaly scan with proper error handling
scan_network() {
    log_message "INFO" "Scanning for unexpected network listeners..."
    
    if ! network_listeners=$(ss -tulnp | grep -v "127.0.0.1" | grep -v ":22" 2>/dev/null); then
        log_message "WARNING" "Failed to check network listeners"
        return 1
    fi
    
    listener_count=$(echo "$network_listeners" | grep -v "^$" | wc -l)
    
    if [ "$listener_count" -gt 0 ]; then
        log_message "ALERT" "Found $listener_count unexpected network listeners"
        echo "$network_listeners" >> "$ALERT_LOG"
        return 2  # Return code 2 indicates suspicious activity
    else
        log_message "INFO" "No unexpected network listeners found"
        return 0
    fi
}

# AI brain invocation with proper error handling
invoke_ai_brain() {
    log_message "INFO" "Checking if AI analysis is needed..."
    
    # Count alert lines
    if [ ! -f "$ALERT_LOG" ]; then
        log_message "INFO" "No alert log found, creating empty file"
        touch "$ALERT_LOG"
        return 0
    fi
    
    alert_count=$(wc -l < "$ALERT_LOG")
    
    # Only invoke AI if we have enough alerts
    if [ "$alert_count" -gt 10 ]; then
        log_message "ALERT" "Alert threshold exceeded ($alert_count lines). Invoking AI brain..."
        
        AI_BRAIN_PATH="$PROJECT_ROOT/core/vigilance/ai_brain.py"
        if [ ! -f "$AI_BRAIN_PATH" ]; then
            log_message "ERROR" "AI brain script not found: $AI_BRAIN_PATH"
            return 1
        fi
        
        if ! python3 "$AI_BRAIN_PATH" 2>> "$LOG_DIR/ai_brain_errors.log"; then
            log_message "ERROR" "AI brain execution failed"
            return 1
        else
            log_message "INFO" "AI brain analysis complete"
            return 0
        fi
    else
        log_message "INFO" "Not enough alerts to trigger AI analysis ($alert_count < 10)"
        return 0
    fi
}

# Main function with timing
main() {
    start_time=$(date +%s)
    log_message "INFO" "===== Vigilance module starting ====="
    
    # Track overall alert status
    alert_triggered=0
    
    # Run checks
    generate_merkle_hash
    if check_integrity; then
        log_message "INFO" "Integrity check passed"
    else
        alert_triggered=1
    fi
    
    if scan_auth_logs; then
        log_message "INFO" "Auth log check passed"
    else
        alert_triggered=1
    fi
    
    if scan_network; then
        log_message "INFO" "Network check passed"
    else
        alert_triggered=1
    fi
    
    # Invoke AI brain if alerts were triggered
    if [ "$alert_triggered" -eq 1 ]; then
        log_message "ALERT" "Alert conditions detected, triggering AI analysis"
        invoke_ai_brain
    fi
    
    end_time=$(date +%s)
    duration=$((end_time - start_time))
    log_message "INFO" "===== Vigilance module completed in $duration seconds ====="
}

# Run main function
main