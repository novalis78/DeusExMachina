#!/bin/bash
# test_ai_wake.sh - Test script to manually trigger AI awakening
# Part of the Deus Ex Machina project

# Import configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Source bash configuration
if [ -f "$PROJECT_ROOT/scripts/bash_config.sh" ]; then
    source "$PROJECT_ROOT/scripts/bash_config.sh"
else
    # Default configuration
    LOG_DIR="/var/log/deus-ex-machina"
    ALERT_LOG="$LOG_DIR/vigilance_alerts.log"
    STATE_FILE="$LOG_DIR/state.json"
fi

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Print welcome message
echo "===== Deus Ex Machina - AI Wake Test ====="
echo "This script will simulate alert conditions to test AI awakening"
echo ""

# Generate simulated alerts
generate_alerts() {
    local count=$1
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo "[${timestamp}] [ALERT] Simulated test alert - manual awakening test" > "$ALERT_LOG"
    
    # Add some specific alert patterns that would trigger analysis
    for i in $(seq 1 $count); do
        echo "[${timestamp}] [ALERT] Suspicious login attempt from IP 192.168.1.${i}" >> "$ALERT_LOG"
        echo "[${timestamp}] [ALERT] Unexpected port 800${i} opened on external interface" >> "$ALERT_LOG"
        echo "[${timestamp}] [ALERT] Configuration file /etc/important${i}.conf was modified" >> "$ALERT_LOG"
    done
    
    echo "Generated $count simulated alert triplets (total alerts: $((count * 3 + 1)))"
}

# Set system state to alert
set_alert_state() {
    echo '{
  "state": "alert",
  "last_transition": "'$(date -Iseconds)'",
  "ttl_seconds": 600
}' > "$STATE_FILE"
    
    echo "System state set to 'alert'"
}

# Run test
run_test() {
    echo "Triggering AI wake sequence..."
    
    # Call vigilance.sh which should trigger ai_brain.py
    if [ -f "$PROJECT_ROOT/core/vigilance/vigilance.sh" ]; then
        echo "Running vigilance module..."
        bash "$PROJECT_ROOT/core/vigilance/vigilance.sh"
    else
        echo "Error: vigilance.sh not found!"
        exit 1
    fi
    
    # Wait a moment for processing
    echo "Waiting for AI analysis to complete..."
    sleep 2
    
    # Check if AI assessment was created
    if [ -f "$LOG_DIR/ai_assessment.json" ]; then
        echo ""
        echo "===== AI HAS AWAKENED ====="
        echo "AI assessment file was created successfully!"
        echo ""
        echo "View the AI's thoughts with:"
        echo "cat $LOG_DIR/ai_assessment.json | jq"
        echo ""
        echo "Check logs for more details:"
        echo "cat $LOG_DIR/ai_brain.log"
    else
        echo ""
        echo "===== AI DID NOT AWAKEN ====="
        echo "No AI assessment file was created."
        echo "Check for errors in the AI brain log:"
        echo "cat $LOG_DIR/ai_brain.log"
    fi
}

# Main execution
echo "Step 1: Generating simulated alerts..."
generate_alerts 5

echo ""
echo "Step 2: Setting system state to 'alert'..."
set_alert_state

echo ""
echo "Step 3: Triggering vigilance and AI brain..."
run_test